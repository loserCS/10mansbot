import asyncio
import datetime
import re
from discord.ext import commands



class ReminderCog(commands.Cog):
    def __init__(self, bot):
        """ Set attributes and remove default help command. """
        self.bot = bot

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

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} Cog has been loaded\n-----")

    @commands.command(case_insensitive = True, aliases = ["remind", "remindme", "remind_me"], usage = 'remind <time> <reminder>', brief = 'Set a reminder to do something')
    async def reminder(self, ctx, time, *, reminder=None):
        #remind = self.guild_reminders[ctx.guild]
        
        
        converted_time = self.convert(time)
        #print(converted_time)

        if converted_time == None:
            #print('converted_time = None')
            await ctx.send('You didnt enter the time correctly (only s, m, h, d are allowed)')
            return
        
        else:
            #print('converted time != None')    
            if converted_time < 1:
                await ctx.send("Time is below minimum duration.\nMinimum duration is 1 Second")
                return

            if converted_time > 86400:
                await ctx.send("Time exceeds maximum duration.\nMaximum duration is 1 day")
                return

            if ctx.message.mentions:
                await ctx.send("Don't mention anyone in your reminder")
                return 

            if ctx.message.role_mentions:
                await ctx.send("Don't mention anyone in your reminder")
                return

            if reminder == None:
                #print('reminder = None')
                reminder = " `No message` "
                await ctx.send(f"Set reminder for **{reminder}**, will ping you in {time}.")

            else:
                await ctx.send(f"Set reminder for **{reminder}** and will ping you in {time}")

            if '@everyone' in reminder:
                await ctx.send("Don't mention anyone in your reminder")
                return 

            if '@here' in reminder:
                await ctx.send("Don't mention anyone in your reminder")
                return 

        await asyncio.sleep(converted_time)
        await ctx.send(f"{ctx.author.mention} Reminder: {reminder}!")
        
def setup(bot):
    bot.add_cog(ReminderCog(bot))