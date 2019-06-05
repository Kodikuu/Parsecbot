from discord.ext import commands
from discord import Color, Embed, utils
import asyncio
import requests
from time import time
import json
from os import path
import re


class eSupport(commands.Cog, name="Support"):

    def __init__(self, bot):
        self.bot = bot
        self.time = 0
        self.run = asyncio.Event(loop=bot.loop)
        self.elist = []
        self.emodify = {}
        self.task = self.bot.loop.create_task(self.scrapeTask())
        self.color = Color(0x5c5cff)

        self.run.set()

        if path.exists('errors.private') and path.isfile('errors.private'):
            with open('errors.private', 'r') as file:
                self.emodify = json.load(file)
                print('Loaded error data')
        else:
            with open('errors.private', 'w') as file:
                json.dump(self.emodify, file)

    def save(self):
        with open('errors.private', 'w') as file:
            json.dump(self.emodify, file)

    async def scrapeTask(self):
        url = "https://support.parsecgaming.com/hc/en-us/sections/115000849851"
        while True:
            await self.run.wait()  # Wait until triggered

            if self.time > time() - 60:
                self.run.clear()
                print("Skipping requested scrape")
                return  # Don't repeat more than once a minute

            print("Performing requested scrape")
            r = requests.get(url)

            data = []
            for item in r.iter_lines():
                if "Error Codes - " in str(item):
                    data.append(str(item))

            errorlist = []
            for i in data:
                tl = {}

                v = "https://support.parsecgaming.com" + i.split("\"")[3][:31]
                tl['url'] = v

                tmp = i.split(">")[1].split("<")[0].replace("&#39;", "'")

                v = [w for w in tmp.split("(")[0].split() if w.isdigit()]
                tl['code'] = v

                tl['title'] = tmp
                tl['desc'] = tmp[len(tmp.split("(")[0])+1:-1]

                errorlist.append(tl)
            self.elist = errorlist

            self.time = time()
            self.run.clear()

    async def checkMessage(self, message):
        # Regex to grab numbers in message,
        # doesn't care about surrounding characters
        nums = [int(a) for a in re.findall(r'\d+', message.content)]

        # Compile a list of matched codes, eventually respond to entire list.
        matched = []

        # Check if a scraped code is present
        for error in self.elist:
            for code in error['code']:
                if int(code) in nums:
                    matched.append(code)

        # Check if a modified code is present
        for code in self.emodify.keys():
            # Duplicates are bad
            if code not in matched:
                # If a numeric code is found in nums
                if code.isdigit() and int(code) in nums:
                    matched.append(code)

                # If a non-numeric code is found in message.content
                elif not code.isdigit() and code in message.content:
                    matched.append(code)

        # For now, only act on the first code (until Process is rewritten)
        return await self.errorProcess(message, matched, False)

    # Check Definitions
    def is_admin():
        async def predicate(ctx):
            # Is the command user trusted?
            role = ["Jedi", "Parsec Team"]
            return any([x in [y.name for y in ctx.author.roles] for x in role])
        return commands.check(predicate)

    @commands.command()
    @is_admin()
    async def scrape(self, ctx):
        self.time = 0
        self.run.set()

    @commands.command()
    async def error(self, ctx, *errorcode):
        # Ensure that the passed argument is a single string in a list/tuple
        code = " ".join(errorcode)
        code = (code, )
        # Just makes things easier when running errorprocess not as a command.
        self.run.set()
        await self.errorProcess(ctx, code, True)

    @commands.command()
    @is_admin()
    async def erroredit(self, ctx, code, key, *desc):
        key = key.lower()

        if key in ["title", "url", "desc", "remove"]:
            if code not in self.emodify.keys():
                self.emodify[code] = {}

            if key == "remove":
                del self.emodify[code]
            else:
                self.emodify[code][key] = ' '.join(desc)

        else:
            await ctx.send("Invalid key to edit")
            return

        self.save()
        await ctx.message.add_reaction("🆗")
        await asyncio.sleep(5)
        await ctx.message.clear_reactions()

    async def errorProcess(self, ctx, matched, explicit=False):

        errors = []

        # Match all found codes
        for code in matched:
            done = False

            # First, scraped errors
            for e in self.elist:
                for ecode in e['code']:
                    if ecode == code:
                        errors.append(e)
                        # Correct error with persistent modifications.
                        if ecode in self.emodify.keys():
                            for key in self.emodify[ecode].keys():
                                errors[-1][key] = self.emodify[ecode][key]
                        done = True
                        break

            else:
                # Second, manual errors. If not already found ('done')
                if code in self.emodify.keys() and not done:
                    errors.append(self.emodify[code])

        else:
            # Third, if no code is found
            if len(errors) == 0:
                # No code found, explicit request
                if explicit:
                    desc = "Please contact staff or correct your error code."
                    emb = Embed(title=f"{matched[0]}: Not Documented.",
                                description=desc,
                                color=self.color)
                    await ctx.channel.send(embed=emb)

                else:
                    # No code found, not an explicit request
                    return False

        # Ensure error is complete, input placeholders if not
        final = []
        for error in errors:
            for key in ["title", "desc", "url"]:
                if key not in error.keys():
                    error[key] = None
            final.append(error)

        # Construct the final embeds
        embeds = []
        for e in final:
            embeds.append(Embed(title=e['title'],
                                url=e['url'],
                                description=e['desc'],
                                color=self.color))

        await self.errorResponse(ctx, embeds, explicit)
        return True

    async def errorResponse(self, ctx, embeds, explicit=False):
        # Attempt to retrieve custom emojis, else use non-custom emojis
        elist = ctx.guild.emojis
        emoji_yes = utils.get(elist, name="supportBotMessage_show") or '✅'
        emoji_no = utils.get(elist, name="supportBotMessage_dontShow") or '❎'

        def check(reaction, user):
            e = reaction.emoji

            return e in (emoji_yes, emoji_no) and not user == self.bot.user

        # Output error immediately if explicit.
        if explicit:
            for embed in embeds:
                await ctx.channel.send(embed=embed)

        else:  # Go through steps if not explicit
            await ctx.add_reaction(emoji_yes)
            await ctx.add_reaction(emoji_no)
            try:
                reaction, user = await self.bot.wait_for('reaction_add',
                                                         timeout=120.0,
                                                         check=check)
            except asyncio.TimeoutError:
                await ctx.clear_reactions()
            else:
                await ctx.clear_reactions()
                if reaction.emoji == emoji_yes:
                    await ctx.add_reaction("🆗")
                    for embed in embeds:
                        await ctx.channel.send(embed=embed)
                    await asyncio.sleep(5)
                    await ctx.clear_reactions()
