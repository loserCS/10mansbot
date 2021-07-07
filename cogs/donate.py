import discord
from discord.ext import commands


class DonateCog(commands.Cog):
    """ Cog to manage interactions with donate links. """

    def __init__(self, bot):
        """ Set attributes """
        self.bot = bot
        self.color = self.bot.color_list[3]
        self.donate_url = self.bot.donate_url

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    @commands.command(brief='Link the bot\'s donation link')
    async def donate(self, ctx):
        description = f'[Click here to donate]({self.donate_url})'
        embed = discord.Embed(title="Donations are greatly appreciated!", description=description, color=self.color)
        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(DonateCog(bot))