# queue.py

import discord
import asyncio
import re
from discord.ext import commands

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

    def __init__(self, bot):
        self.bot = bot
        self.guild_queues = {}
        self.color = self.bot.color_list[3]
        
    

    def convert(self, time):
        pos = ['s', 'sec', 'secs', 'm', 'min', 'mins', 'h', 'hr', 'hrs', 'd', 'day']
        temp = re.compile("([0-9]+)([a-zA-Z]+)")
        #print(ctx.author)
        try:
            res = temp.match(time).groups()
        except:
            converted_time = None
            #print(f'{time} exception 1')
            return converted_time
        
        intres = int(res[0])

        #print(str(res))
        if res[1] in pos:
            #print('yeah yeah(dababy)')

            time_dict = {"s": 1, "sec": 1, "secs": 1, "m": 60, "min": 60, "mins": 60, "h": 3600, "hr": 3600, "hrs": 3600, "d": 86400, "day": 86400}
            unit = res[1]
            #print(time_dict[unit])


        #print(intres * int(time_dict[unit]))
        return intres * int(time_dict[unit])

    async def get_queue(self, guild):
        queue = await self.bot.queue.find(guild.id)
        gqueue = self.guild_queues[guild]
        #print(queue)
        if queue is None:
            data = {"_id": guild.id, "active": [], "bursted": [], "banned": [], "capacity": 10}
            await self.bot.queue.upsert(data)
            return
        gqueue.active = [self.bot.get_user(id) for id in queue['active'] if self.bot.get_user(id)]
        gqueue.bursted = [self.bot.get_user(id) for id in queue['bursted'] if self.bot.get_user(id)]
        gqueue.banned = [self.bot.get_user(id) for id in queue['banned'] if self.bot.get_user(id)]
        gqueue.capacity = queue['capacity']
        #print(gqueue.active)

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize an empty list for each guild the bot is in"""
        for guild in self.bot.guilds:
            if guild not in self.guild_queues:  # Don't add empty queue if guild already loaded
                self.guild_queues[guild] = QQueue()            
            await self.get_queue(guild)

        print(f"{self.__class__.__name__} Cog has been loaded\n-----")
            

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty list for guilds that are added"""
        self.guild_queues[guild] = QQueue()
        data = await self.bot.queue.find(guild.id)
        if data is None:
            data = {"_id": self.guild.id, "active": [], "bursted": [], "banned": [], "capacity": 10}
            await self.bot.queue.upsert(data)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Remove queue list when a guild is removed."""
        self.guild_queues.pop(guild)
        await self.bot.queue.delete(guild.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        queue = self.guild_queues[member.guild]
        if member in queue.active:
            queue.active.remove(member)
            data = {
                '_id': member.guild.id,
                'active': member.id
            }
            await self.bot.queue.upsert(data, "pull")


        
    
    def queue_embed(self, guild, title=None):
        queue = self.guild_queues[guild]

        if title:
            title += f'({len(queue.active)}/{queue.capacity})'

        if queue.active != []: #if there are users in the queue
            queue_str = ''.join(f'{e_usr[0]}. {e_usr[1].mention}\n' for e_usr in enumerate(queue.active, start=1))
        else: #no users in queue
            queue_str = '_The queue is empty..._'

        embed = discord.Embed(title=title, description=queue_str, color=self.color)
        embed.set_footer(text='Users will be pinged when the queue fills')
        return embed
    
    async def burst_queue(self, guild):
        queue = self.guild_queues[guild]
        for user in queue.bursted:
            data = {
                '_id': guild.id,
                'bursted': user.id
            }
            await self.bot.queue.upsert(data, "pull")

        queue.bursted = queue.active
        for user in queue.bursted:
            data = {
                '_id': guild.id,
                'bursted': user.id,
            }
            await self.bot.queue.upsert(data, "push")

        for user in queue.active:
            data = {
                '_id': guild.id,
                'active': user.id
            }
            await self.bot.queue.upsert(data, "pull")

        queue.active = []
        user_mentions = ''.join(user.mention for user in queue.bursted)
        popflash_cog = self.bot.get_cog('PopflashCog')

        if popflash_cog:
            popflash_url = popflash_cog.get_popflash_url(guild)
            description = f'[Join the PopFlash lobby here]({popflash_url})'
        else:
            description = f'{queue.capacity} people have joined the queue'    

        pop_embed = discord.Embed(title='Holy crap..... the queue has pooped....😱😱😱', description=description, color=self.color)
        return pop_embed, user_mentions

    def banned_embed(self, guild, title=None):
        queue = self.guild_queues[guild]

        if queue.banned !=[]: #there are users banned 
            banned_str = ''.join(f'{e_usr[0]}. {e_usr[1].mention}\n' for e_usr in enumerate(queue.banned, start=1))
        else: #no users banned
            banned_str = '_No users are currently banned_'
        embed = discord.Embed(title='Users currently banned', description=banned_str, color=self.color)
        return embed

    @commands.command(brief='Join the queue', aliases=['john', 'jon'])
    async def join(self, ctx):
        """check if member can be added to the guild queue and then add them if so"""
        queue = self.guild_queues[ctx.guild]

        if ctx.author in queue.active:
            title = f'**{ctx.author.display_name}** is already in the queue '
        elif ctx.author in queue.banned:
            title = f'**{ctx.author.display_name}** is banned from queueing '
        elif len(queue.active) >= queue.capacity: # queue full
            title = f'Unable to added **{ctx.author.display_name}**: Queue is full'
        else: #open spot in queue
            queue.active.append(ctx.author)
            title = f'**{ctx.author.display_name}** has been added to the queue '
            data = {
                '_id': ctx.guild.id,
                'active': ctx.author.id,
            }
            await self.bot.queue.upsert(data, "push")
            
        #check and burst queue if full
        if len(queue.active) == queue.capacity:
            embed, user_mentions = await self.burst_queue(ctx.guild)
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
    async def leave(self, ctx, time=None):
        """check if the member can be removed from the guild queue and remove them if so"""
        #print(time)
        queue = self.guild_queues[ctx.guild]
        converted_time = self.convert(time)
        data = {
                '_id': ctx.guild.id,
                'active': ctx.author.id
            }
        #print(converted_time)

        if converted_time == None:
            #print('this is firing')
            if ctx.author in queue.active:
                queue.active.remove(ctx.author)
                await self.bot.queue.upsert(data, "pull")
                title = f'**{ctx.author.display_name}** has left the queue '
                #print({ctx.author})

            elif ctx.author not in queue.active:
                title = f'**{ctx.author.display_name}** isn\'t in the queue '
        
            embed = self.queue_embed(ctx.guild, title)
            if queue.last_msg:
                try:
                    await queue.last_msg.delete()
                except discord.errors.NotFound:
                    pass

        elif time:
            if converted_time < 1:
                await ctx.send("Time is below minimum duration.\nMinimum duration is 1 Second")
                return

            if converted_time > 86400:
                await ctx.send("Time exceeds maximum duration.\nMaximum duration is 1 day")
                return

            if ctx.author not in queue.active:
                title = f'**{ctx.author.display_name}** isn\'t in the queue '
                
            else:
                await ctx.send(f'Removing {ctx.author.display_name} from the queue in {time}')
                await asyncio.sleep(converted_time)
                if ctx.author in queue.active:
                    queue.active.remove(ctx.author)
                    await self.bot.queue.upsert(data, "pull")
                    
                    title = f'**{ctx.author.display_name}** has been removed from the queue after {time} '
        
            embed = self.queue_embed(ctx.guild, title)
            if queue.last_msg:
                try:
                    await queue.last_msg.delete()
                except discord.errors.NotFound:
                    pass


        queue.last_msg = await ctx.channel.send(embed = embed)

    @commands.command(brief='Display who is currently in the queue')
    async def view(self, ctx):
        """ Display the queue as an embed list of mentioned names"""
        queue = self.guild_queues[ctx.guild]
        embed = self.queue_embed(ctx.guild, 'Players in queue ')

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
            data = {
                '_id': ctx.guild.id,
                'active': removee.id
            }
            if removee in queue.active:
                queue.active.remove(removee)
                await self.bot.queue.upsert(data, "pull")
                title = f'**{removee.display_name}** has been removed from the queue '
            elif queue.bursted and removee in queue.bursted:
                data = {
                    '_id': ctx.guild.id,
                    'bursted': removee.id
                }
                queue.bursted.remove(removee)
                await self.bot.queue.upsert(data, "pull")

                if len(queue.active) >=1:
                    await ctx.trigger_typing()  # Need to retrigger typing for second send
                    saved_queue = queue.active.copy()
                    first_in_queue = saved_queue[0]
                    queue.active = queue.bursted + [first_in_queue]
                    queue.bursted = []
                    pop_embed, user_mentions = self.burst_queue(ctx.guild)
                    await ctx.send(user_mentions, embed=pop_embed)

                    if len(queue.active) >1:
                        queue.active = saved_queue[1:]

                    return
                else:
                    queue.active = queue.bursted
                    for user in queue.bursted:
                        data = {
                            '_id': ctx.guild.id,
                            'bursted': user.id
                        }
                        await self.bot.queue.upsert(data, 'pull')
                    for user in queue.active:
                        data = {
                            '_id': ctx.guild.id,
                            'active': user.id
                        }
                        await self.bot.queue.upsert(data, "push")
                    queue.bursted = []
                    title= f'**{removee.display_name}** has been removed from the most recent filled queue '

            else:
                title = f'**{removee.display_name}** is not in the queue or the most recent filled queue'
            
            embed = self.queue_embed(ctx.guild, title)

            if queue.last_msg: 
                try:
                    await queue.last_msg.delete()
                except discord.errors.NotFound:
                    pass
                
            queue.last_msg = await ctx.send(embed=embed)

    @commands.command(brief='Empty the queue (must have server kick perms)',
                      aliases=['clear',])
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """Reset the guild queue list to empty. """
        queue = self.guild_queues[ctx.guild]
        for user in queue.active:
            data = {
                '_id': ctx.guild.id,
                'active': user.id
            }
            await self.bot.queue.upsert(data, "pull")
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
        """ Respond to permissions error with explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot remove players without {missing_perm} permission.'
            embed = discord.Embed(title=title, color=self.color)
            await ctx.send(embed=embed)

    @commands.command(brief='Set the capacity of the queue (Must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def cap(self, ctx, new_cap):
        """Set the queue capacity"""
        try:
            new_cap = int(new_cap)
        except ValueError:
            embed = discord.Embed(title=f'{new_cap} is not an integer', color = self.color)
        else:
            if new_cap < 2 or new_cap > 100:
                embed = discord.Embed(title='Capacity is out of valid range', color=self.color)
            else: 
                self.guild_queues[ctx.guild].capacity = new_cap
                await self.bot.queue.upsert({"_id": ctx.guild.id, "capacity": new_cap})
                embed = discord.Embed(title=f'Queue capacity set to {new_cap}', color=self.color)

        await ctx.send(embed=embed)

    @cap.error
    async def cap_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot change queue capacity without {missing_perm} permission'
            embed = discord.Embed(title=title, color=self.color)
            await ctx.send(embed=embed)


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
        

        # Set unban time if there were time arguments
        #time_delta = timedelta(**time_delta_values)
        #unban_time = None if time_delta_values == {} else datetime.now(timezone.utc) + time_delta

        # Insert mentions into ban table
        banee = ctx.message.mentions[0]
        if banee in queue.banned:
            await ctx.send(f'**{banee.display_name}** is already banned')
            return

        queue.banned.append(banee)
        
        data = {
            '_id': ctx.guild.id,
            'banned': banee.id
        }
        await self.bot.queue.upsert(data, "push")

        # Remove banned users from the queue
        if banee in queue.active:
            queue.active.remove(banee)
            data ={
                '_id': ctx.guild.id,
                'active': banee.id
            }
            await self.bot.queue.upsert(data, "pull")

        # Generate embed and send message
        banned_users_str = ', '.join(f'**{user.display_name}**' for user in ctx.message.mentions)
        #ban_time_str = '' if unban_time is None else f' for {self.timedelta_str(time_delta)}'
        embed = discord.Embed(title=f'Banned {banned_users_str}')
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
            data = {
                '_id': ctx.guild.id,
                'banned': ctx.message.mentions[0].id
            }
            await self.bot.queue.upsert(data, "pull")
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

        
def setup(bot):
    bot.add_cog(QueueCog(bot))