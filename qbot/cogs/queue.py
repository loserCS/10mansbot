# queue.py

from discord.ext import commands
import discord
import asyncio
from datetime import datetime, timedelta, timezone
import re


class QQueue:
    """ Queue class for the bot. """

    def __init__(self, active=None, capacity=10, bursted=None, timeout=None, last_msg=None, banned=None):
        """ Set attributes. """
        # Assign empty lists inside function to make them unique to objects
        self.active = [] if active is None else active  # List of players in the queue
        self.capacity = capacity  # Max queue size
        self.bursted = [] if bursted is None else bursted  # Cached last filled queue
        self.banned = [] if banned is None else banned
        # self.timeout = timeout  # Number of minutes of inactivity after which to empty the queue
        self.last_msg = last_msg  # Last sent confirmation message for the join command

    @property
    def is_default(self):
        """ Indicate whether the QQueue has any non-default values. """
        return self.active == [] and self.capacity == 10 and self.bursted == []


class QueueCog(commands.Cog):
    """ Cog to manage queues of players among multiple servers. """
    
    time_arg_pattern = re.compile(r'\b((?:(?P<days>[0-9]+)d)|(?:(?P<hours>[0-9]+)h)|(?:(?P<minutes>[0-9]+)m))\b')

    def __init__(self, bot, color):
        """ Set attributes. """
        self.bot = bot
        self.guild_queues = {}  # Maps Guild -> QQueue
        self.color = color

    @commands.Cog.listener()
    async def on_ready(self):
        """ Initialize an empty list for each guild the bot is in. """
        for guild in self.bot.guilds:
            if guild not in self.guild_queues:  # Don't add empty queue if guild already loaded
                self.guild_queues[guild] = QQueue()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty list for guilds that are added. """
        self.guild_queues[guild] = QQueue()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Remove queue list when a guild is removed. """
        self.guild_queues.pop(guild)

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    def queue_embed(self, guild, title=None):
        """"""
        queue = self.guild_queues[guild]

        if title:
            title += f' ({len(queue.active)}/{queue.capacity})'

        if queue.active != []:  # If there are users in the queue
            queue_str = ''.join(f'{e_usr[0]}. {e_usr[1].mention}\n' for e_usr in enumerate(queue.active, start=1))
        else:  # No users in queue
            queue_str = '_The queue is empty..._'

        embed = discord.Embed(title=title, description=queue_str, color=self.color)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    def burst_queue(self, guild):
        queue = self.guild_queues[guild]
        queue.bursted = queue.active  # Save bursted queue for player draft
        queue.active = []  # Reset the player queue to empty
        user_mentions = ''.join(user.mention for user in queue.bursted)
        popflash_cog = self.bot.get_cog('PopflashCog')

        if popflash_cog:
            popflash_url = popflash_cog.get_popflash_url(guild)
            description = f'[Join the PopFlash lobby here]({popflash_url})'
        else:
            description = ''

        pop_embed = discord.Embed(title='Holy crap..... the queue has pooped....', description=description, color=self.color)
        return pop_embed, user_mentions

    def banned_embed(self, guild, title=None):
        queue = self.guild_queues[guild]

        if queue.banned !=[]: #there are users banned 
            banned_str = ''.join(f'{e_usr[0]}. {e_usr[1].mention}\n' for e_usr in enumerate(queue.banned, start=1))
        else: #no users banned
            banned_str = '_No users are currently banned_'
        embed = discord.Embed(title='Users currently banned', description=banned_str, color=self.color)
        return embed

    @commands.command(brief='Join the queue')
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so. """
        queue = self.guild_queues[ctx.guild]

        if ctx.author in queue.active:  # Author already in queue
            title = f'**{ctx.author.display_name}** is already in the queue'
        elif ctx.author in queue.banned:
            title = f'**{ctx.author.display_name}** is banned from queueing '
        elif len(queue.active) >= queue.capacity:  # Queue full
            title = f'Unable to add **{ctx.author.display_name}**: Queue is full'
        else:  # Open spot in queue
            queue.active.append(ctx.author)
            title = f'**{ctx.author.display_name}** has been added to the queue'

        # Check and burst queue if full
        if len(queue.active) == queue.capacity:
            embed, user_mentions = self.burst_queue(ctx.guild)
            await ctx.send(user_mentions, embed=embed)
        else:
            embed = self.queue_embed(ctx.guild, title)

            if queue.last_msg:
                try:
                    await queue.last_msg.delete()
                except discord.errors.NotFound:
                    pass

            queue.last_msg = await ctx.send(embed=embed)

    @commands.command(brief='Leave the queue (or the bursted queue)')
    async def leave(self, ctx):
        """ Check if the member can be remobed from the guild and remove them if so. """
        queue = self.guild_queues[ctx.guild]

        if ctx.author in queue.active:
            queue.active.remove(ctx.author)
            title = f'**{ctx.author.display_name}** has been removed from the queue '
        else:
            title = f'**{ctx.author.display_name}** isn\'t in the queue '

        embed = self.queue_embed(ctx.guild, title)

        if queue.last_msg:
            try:
                await queue.last_msg.delete()
            except discord.errors.NotFound:
                pass

        queue.last_msg = await ctx.channel.send(embed=embed)

    @commands.command(brief='Display who is currently in the queue')
    async def view(self, ctx):
        """  Display the queue as an embed list of mentioned names. """
        queue = self.guild_queues[ctx.guild]
        embed = self.queue_embed(ctx.guild, 'Players in queue')

        if queue.last_msg:
            try:
                await queue.last_msg.delete()
            except discord.errors.NotFound:
                pass

        queue.last_msg = await ctx.send(embed=embed)

    @commands.command(usage='remove <user mention>',
                      brief='Remove the mentioned user from the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def remove(self, ctx):
        try:
            removee = ctx.message.mentions[0]
        except IndexError:
            embed = discord.Embed(title='Mention a player in the command to remove them', color=self.color)
            await ctx.send(embed=embed)
        else:
            queue = self.guild_queues[ctx.guild]

            if removee in queue.active:
                queue.active.remove(removee)
                title = f'**{removee.display_name}** has been removed from the queue'
            elif queue.bursted and removee in queue.bursted:
                queue.bursted.remove(removee)

                if len(queue.active) >= 1:
                    # await ctx.trigger_typing()  # Need to retrigger typing for second send
                    saved_queue = queue.active.copy()
                    first_in_queue = saved_queue[0]
                    queue.active = queue.bursted + [first_in_queue]
                    queue.bursted = []
                    pop_embed, user_mentions = self.burst_queue(ctx.guild)
                    await ctx.send(user_mentions, embed=pop_embed)

                    if len(queue.active) > 1:
                        queue.active = saved_queue[1:]

                    return
                else:
                    queue.active = queue.bursted
                    queue.bursted = []
                    title = f'**{removee.display_name}** has been removed from the most recent filled queue'

            else:
                title = f'**{removee.display_name}** is not in the queue or the most recent filled queue'

            embed = self.queue_embed(ctx.guild, title)

            if queue.last_msg:
                try:
                    await queue.last_msg.delete()
                except discord.errors.NotFound:
                    pass

            queue.last_msg = await ctx.send(embed=embed)

    @commands.command(brief='Empty the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """ Reset the guild queue list to empty. """
        queue = self.guild_queues[ctx.guild]
        queue.active.clear()
        embed = self.queue_embed(ctx.guild, 'This is so sad..... no 10 man tonight 😔')

        if queue.last_msg:
            try:
                await queue.last_msg.delete()
            except discord.errors.NotFound:
                pass

        queue.last_msg = await ctx.send(embed=embed)

    @remove.error
    @empty.error
    async def remove_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot remove players without {missing_perm} permission!'
            embed = discord.Embed(title=title, color=self.color)
            await ctx.send(embed=embed)

    @commands.command(brief='Set the capacity of the queue (Must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def cap(self, ctx, new_cap):
        """ Set the queue capacity. """
        try:
            new_cap = int(new_cap)
        except ValueError:
            embed = discord.Embed(title=f'{new_cap} is not an integer', color=self.color)
        else:
            if new_cap < 2 or new_cap > 100:
                embed = discord.Embed(title='Capacity is outside of valid range', color=self.color)
            else:
                self.guild_queues[ctx.guild].capacity = new_cap
                embed = discord.Embed(title=f'Queue capacity set to {new_cap}', color=self.color)

        await ctx.send(embed=embed)

    @cap.error
    async def cap_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot change queue capacity without {missing_perm} permission!'
            embed = discord.Embed(title=title, color=self.color)
            await ctx.send(embed=embed)

    @staticmethod
    def timedelta_str(tdelta):
        """ Convert time delta object to a worded string representation with only days, hours and minutes. """
        conversions = (('days', 86400), ('hours', 3600), ('minutes', 60))
        secs_left = int(tdelta.total_seconds())
        unit_strings = []

        for unit, conversion in conversions:
            unit_val, secs_left = divmod(secs_left, conversion)

            if unit_val != 0 or (unit == 'minutes' and len(unit_strings) == 0):
                unit_strings.append(f'{unit_val} {unit}')

        return ', '.join(unit_strings)

    @commands.command(usage='ban <user mention>',
                      brief='Ban all mentioned users from joining the queue (need server ban perms)')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, *args):
        """ Ban users mentioned in the command from joining the queue for a certain amount of time or indefinitely. """
        # Check that users are mentioned
        queue = self.guild_queues[ctx.guild]
        if len(ctx.message.mentions) == 0:
            embed = discord.Embed(title='Mention a user in the command to ban them')
            await ctx.send(embed=embed)
            return
        

        # Parse the time arguments
        time_units = ('days', 'hours', 'minutes')
        time_delta_values = {}  # Holds the values for each time unit arg

        for match in self.time_arg_pattern.finditer(ctx.message.content):  # Iterate over the time argument matches
            for time_unit in time_units:  # Figure out which time unit this match is for
                time_value = match.group(time_unit)  # Get the value for this unit

                if time_value is not None:  # Check if there is an actual group value
                    time_delta_values[time_unit] = int(time_value)
                    break  # There is only ever one group value per match

        # Set unban time if there were time arguments
        time_delta = timedelta(**time_delta_values)
        unban_time = None if time_delta_values == {} else datetime.now(timezone.utc) + time_delta

        # Insert mentions into ban table
        queue.banned.append(ctx.message.mentions[0])

        # Remove banned users from the queue
        banee = ctx.message.mentions[0]
        if banee in queue.active:
            queue.active.remove(banee)

        # Generate embed and send message
        banned_users_str = ', '.join(f'**{user.display_name}**' for user in ctx.message.mentions)
        ban_time_str = '' if unban_time is None else f' for {self.timedelta_str(time_delta)}'
        embed = discord.Embed(title=f'Banned {banned_users_str}{ban_time_str}')
        embed.set_footer(text='Banned users have been removed from the queue')
        await ctx.send(embed=embed)


        #await asyncio.sleep(time_delta)
        #unban_time_str = '' if unban_time is None else f' for {self.timedelta_str(time_delta)}'
        #embed = discord.Embed(title=f'Unbanned {banned_users_str}{unban_time_str}')
        #await ctx.send(embed=embed)
        #queue.banned.remove(banee)


    @commands.command(usage='unban <user mention> ...',
                      brief='Unban all mentioned users so they can join the queue (need server ban perms)')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx):
        """ Unban users mentioned in the command so they can join the queue. """
        # Check that users are mentioned
        queue = self.guild_queues[ctx.guild]
        if len(ctx.message.mentions) == 0:
            embed = discord.Embed(title='Mention a user in the command to unban them')
            await ctx.send(embed=embed)
            return

        # Delete users from the ban table
        unbanned_users = ctx.message.mentions[0]
        if unbanned_users in queue.banned:
            queue.banned.remove(unbanned_users)
            embed = discord.Embed(title=f'Unbanned **{unbanned_users.display_name}** ')
        else:
            embed = discord.Embed(title=f'{unbanned_users.display_name} was not on the banned list')

        embed.set_footer(text='Unbanned users may now join the queue')
        await ctx.send(embed=embed)

    @commands.command(brief='Display who is currently banned from the queue')
    async def banlist(self, ctx):
        """ Display the queue as an embed list of mentioned names"""
        queue = self.guild_queues[ctx.guild]
        embed = self.banned_embed(ctx.guild, "Users currently banned. ")
        if queue.last_msg:
            try:
                await queue.last_msg.delete()
            except discord.errors.NotFound:
                pass
        queue.last_msg = await ctx.send(embed=embed)
