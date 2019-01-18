# Core Requirements
from discord.ext import commands
from discord import Activity, ActivityType, AppInfo, Color, Embed
import asyncio

# Uncomment this with a full IDE, it should warn that it's not in use
# The idea being that we never import EVERYTHING. We don't need it all
# import discord

# File IO (Cryptographically Insecure)
import json
from os import path

# Timers
from time import time
import datetime

# Error code scraping
import requests

# Additional Requirements

# Pre-start configuration and token loading
if path.exists('core.private') and path.isfile('core.private'):
    with open('core.private', 'r') as file:
        core = json.load(file)

    if 'token' not in core.keys():
        print('Token Missing.')
        core['token'] = input('Token: ')
        with open('core.private', 'w') as file:
            json.dump(core, file)
else:
    print('Core data is missing.')

    token = input('Token: ')
    if token == '':
        raise ValueError('Invalid Token: Empty String')

    core = {'token': token,
            }
    del token  # We don't want extra auth token copies lying around.

    with open('core.private', 'x') as file:
        json.dump(core, file)

# Pre-start setup
bot = commands.AutoShardedBot(command_prefix=commands.when_mentioned_or('>'))
bot.activity = Activity(type=ActivityType.watching,
                        name='Parsec develop.')
state = {'state': 'starting',
         'persistent': {},
         'client': bot,
         'ready_event': asyncio.Event(loop=bot.loop),
         'etime': 0
         }

if path.exists('persistence.private') and path.isfile('persistence.private'):
    with open('persistence.private', 'r') as file:
        state['persistent'] = json.load(file)
        print('Loaded persistent data')
else:
    with open('persistence.private', 'x') as file:
        json.dump(state['persistent'], file)


# Function + Event Definitions

async def errorScrape(url=None):
    if state['etime'] > time() - 60:
        return  # Don't repeat more than once a minute
    if url is None:
        url = "https://support.parsecgaming.com/hc/en-us/sections/115000849851"
    r = requests.get(url)

    data = []
    for item in r.iter_lines():
        if "Error Codes - " in str(item):
            data.append(str(item))

    errorlist = []
    for item in data:
        tl = {}

        val = "https://support.parsecgaming.com" + item.split("\"")[1][:31]
        tl['url'] = val

        tmp = item.split(">")[1].split("<")[0].replace("&#39;", "'")

        val = [word for word in tmp.split("(")[0].split() if word.isdigit()]
        tl['code'] = val

        tl['title'] = tmp
        tl['desc'] = tmp[len(tmp.split("(")[0])+1:-1]

        errorlist.append(tl)
        state['elist'] = errorlist


@bot.event
async def on_message(message):
    # Return if bot message
    if message.author == bot.user:
        return

    if not (message.content.startswith(">") or bot.user in message.mentions):
        # Look for error codes if a command isn't used.
        tmp = message.content.split()
        for i in tmp:
            if i.isdigit() or i in state['persistent']['errors'].keys():
                # If any 'word' in the message is a number, or a manual error.
                await errorScrape()
                await errorProcess(message, i, False)
                return

        # Look for error phrases if a command isn't used.
        for code in state['persistent']['errors'].keys():
            if code.lower() in message.content.lower():
                await errorScrape()
                await errorProcess(message, code, False)
                return

    await bot.process_commands(message)


async def saveP():
    with open('persistence.private', 'w') as file:
        json.dump(state['persistent'], file)


@bot.command()
async def error(ctx, errorcode):
    # Just makes things easier when running errorprocess not as a command.
    await errorScrape()
    await errorProcess(ctx, errorcode, True)


async def errorProcess(ctx, errorcode, explicit=False):
    def check(reaction, user):
        e = str(reaction.emoji)
        return e == '❎' or e == '✅' and not user == bot.user

    # Get scraped error
    error = None
    for e in state['elist']:
        if error is not None:
            break
        for code in e['code']:
            if errorcode == code:
                error = e
                # Correct error with persistent modifications.
                if errorcode in state["persistent"]["errors"].keys():
                    for key in state["persistent"]["errors"][errorcode].keys():
                        error[key] = state["persistent"]["errors"][errorcode][key]
                break
    else:
        # Search through persistence data for manually added key
        if errorcode in state["persistent"]["errors"].keys():
            error = state["persistent"]["errors"][errorcode]

        else:
            if explicit:
                emb = Embed(title=f"{errorcode} Not Documented.",
                            description="Please contact staff or correct your error code.",
                            timestamp=datetime.datetime.now(),
                            color=Color.dark_red())
                await ctx.channel.send(embed=emb)
            return  # No error found

    # Ensure error is complete, input placeholders if not
    for key in ["title", "desc", "url"]:
        if key not in error.keys():
            error[key] = ""

    # Output error immediately if explicit.
    if explicit:
        rembed = Embed(title=error['title'],
                       description=error['desc'],
                       url=error['url'],
                       timestamp=datetime.datetime.now(),
                       color=Color.dark_red())
        await ctx.channel.send(embed=rembed)

    else:  # Go through steps if not explicit
        await ctx.add_reaction("❎")
        await ctx.add_reaction("✅")
        try:
            reaction, user = await bot.wait_for('reaction_add',
                                                timeout=60.0,
                                                check=check)
        except asyncio.TimeoutError:
            await ctx.clear_reactions()
        else:
            await ctx.clear_reactions()
            if str(reaction.emoji) == '✅':
                await ctx.add_reaction("🆗")
                rembed = Embed(title=error['title'],
                               description=error['desc'],
                               url=error['url'],
                               timestamp=datetime.datetime.now(),
                               color=Color.dark_red())
                await ctx.channel.send(embed=rembed)
                await asyncio.sleep(5)
                await ctx.clear_reactions()


@bot.command()
async def erroredit(ctx, code, key, *desc):
    if "errors" not in state["persistent"].keys():
        state["persistent"]["errors"] = {}

    if key not in ["title", "url", "desc", "remove"]:
        ctx.send("Invalid key to edit")

    if key == "remove":
        del state["persistent"]["errors"][code]
        return

    if code not in state["persistent"]["errors"].keys():
        state["persistent"]["errors"][code] = {}

    state["persistent"]["errors"][code][key] = ' '.join(desc)
    await saveP()
    await ctx.message.add_reaction("🆗")
    await asyncio.sleep(5)
    await ctx.message.clear_reactions()


@bot.command()
async def latency(ctx):
    val = round(bot.latency, 5)
    await ctx.send(f'Latency: {val}ms')


@bot.command(description='Restart the bot.')
async def restart(ctx):
    await ctx.send('Restarting.')
    exit()


@bot.command(description='Shut down the bot.', hidden=True)
@commands.is_owner()
async def quit(ctx):
    await ctx.send('Shutting Down.')
    state['state'] = 'shutdown'
    await bot.logout()


@quit.error
async def quit_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(f'Only {AppInfo.owner} may shut me down.')
    elif ctx.author.id == bot.owner_id:
        await ctx.send('Something went very *very* ***wrong.***')

# Start bot
print('Starting Bot')

bot.run(core['token'])

if state['state'] == 'shutdown':
    exit(0x78)
else:
    exit()
