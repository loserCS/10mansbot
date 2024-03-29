import discord
from discord.ext import commands
import Levenshtein as lev
GITHUB = 'https://github.com/loserCS/10mansbot'  # TODO: Use git API to get link to repo?


class HelpCog(commands.Cog):
    """ Handles everything related to the help menu. """

    def __init__(self, bot):
        """ Set attributes and remove default help command. """
        self.bot = bot
        self.color = self.bot.color_list[3]
        #self.logo = 'https://raw.githubusercontent.com/'
        self.bot.remove_command('help')

    def help_embed(self, title):
        embed = discord.Embed(title=title, color=self.color)
        prefix = self.bot.command_prefix
        prefix = prefix[0] if prefix is not str else prefix

        for cog in self.bot.cogs:  # Uset bot.cogs instead of bot.commands to control ordering in the help embed
            if cog == "CacherCog":
                continue
            else:
                for cmd in self.bot.get_cog(cog).get_commands():
                    if cmd.usage:  # Command has usage attribute set
                        embed.add_field(name=f'**{prefix}{cmd.usage}**', value=f'_{cmd.brief}_', inline=False)
                    else:
                        embed.add_field(name=f'**{prefix}{cmd.name}**', value=f'_{cmd.brief}_', inline=False)

        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        """ Set presence to let users know the help command. """
        activity = discord.Activity(type=discord.ActivityType.watching, name="for q!help")
        await self.bot.change_presence(activity=activity)
        print(f"{self.__class__.__name__} Cog has been loaded\n-----")

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """ Send help message when a mis-entered command is received. """
        if type(error) is commands.CommandNotFound:
            # Get Levenshtein distance from commands
            in_cmd = ctx.invoked_with
            bot_cmds = list(self.bot.commands)
            lev_dists = [lev.distance(in_cmd, str(cmd)) / max(len(in_cmd), len(str(cmd))) for cmd in bot_cmds]
            lev_min = min(lev_dists)

            # Prep help message title
            embed_title = f'**```{ctx.message.content}```** is not valid!'
            prefix = self.bot.command_prefix
            prefix = prefix[0] if prefix is not str else prefix

            # Make suggestion if lowest Levenshtein distance is under threshold
            if lev_min <= 0.5:
                embed_title += f' Did you mean `{prefix}{bot_cmds[lev_dists.index(lev_min)]}`?'
            else:
                embed_title += f' Use `{prefix}help` for a list of commands'

            embed = discord.Embed(title=embed_title, color=self.color)
            await ctx.send(embed=embed)

    @commands.command(brief='Display the help menu')  # TODO: Add 'or details of the specified command'
    async def help(self, ctx):
        """ Generate and send help embed based on the bot's commands. """
        embed = self.help_embed('__Queue Bot Commands__')
        await ctx.send(embed=embed)

    @commands.command(brief='Display basic info about this bot')
    async def info(self, ctx):
        """ Display the info embed. """
        description = '_Bot used for among us queues_\n'


        description += f'\nSource code can be found [here]({GITHUB}) on GitHub'
        embed = discord.Embed(title='__Among Us Queue Bot__', description=description, color=self.color)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(HelpCog(bot))