import asyncio
from discord.ext import commands



class ReminderCog(commands.Cog):
    def __init__(self, bot):
        """ Set attributes and remove default help command. """
        self.bot = bot

    @commands.command(case_insensitive = True, aliases = ["remind", "remindme", "remind_me"])
    async def reminder(self, ctx, time, *, reminder):
        def convert(time):
            pos = ['s', 'm', 'h', 'd']

            time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600*24}

            unit = time[-1]

            if unit not in pos:
                return -1
            try:
                val = int(time[:-1])
            except:
                return -2

            return val * time_dict[unit]
        
        converted_time = convert(time)

        if converted_time == -1:
            await ctx.send('You didnt enter the time correctly')
            return
        
        if converted_time == -2:
            await ctx.send("Time must be an integer")
            return

        await ctx.send(f"Set reminder for **{reminder}** and will ping you in {time}")

        await asyncio.sleep(converted_time)
        await ctx.send(f"{ctx.author.mention} Reminder: {reminder}!")