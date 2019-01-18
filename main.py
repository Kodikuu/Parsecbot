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

    # Look for error codes if a command isn't used.
    if not (message.content.startswith(">") or bot.user in message.mentions):
        tmp = message.content.split()
        for i in tmp:
            if i.isdigit():  # If any 'word' in the message is a number.
                await errorScrape()
                for error in state['elist']:
                    for code in error['code']:
                        if i == code:
                            await handleCode(message, error)
    await bot.process_commands(message)


async def handleCode(message, error):
    def check(reaction, user):
        e = str(reaction.emoji)
        return e == '❎' or e == '✅' and not user == bot.user

    await message.add_reaction("❎")
    await message.add_reaction("✅")
    try:
        reaction, user = await bot.wait_for('reaction_add',
                                            timeout=60.0,
                                            check=check)
    except asyncio.TimeoutError:
        await message.clear_reactions()
    else:
        await message.clear_reactions()
        if str(reaction.emoji) == '✅':
            await message.add_reaction("🆗")
            # await message.channel.send(f"{error['title']}, <{error['url']}>")
            rembed = Embed(title=f"[{error['title']}]({error['url']})",
                           timestamp=datetime.datetime.now(),
                           color=Color.dark_red())
            await message.channel.send(embed=rembed)
            await asyncio.sleep(5)
            await message.clear_reactions()


@bot.command()
async def error(ctx, errorcode):
    await errorScrape()
    for error in state['elist']:
        for code in error['code']:
            if errorcode == code:
                emb = Embed(title=f"[{error['title']}]({error['url']})",
                            timestamp=datetime.datetime.now(),
                            color=Color.dark_red())
                await ctx.channel.send(embed=emb)
                return
    else:
        emb = Embed(title=f"{errorcode} Not Documented.",
                    description="Please contact staff or correct your error code.",
                    timestamp=datetime.datetime.now(),
                    color=Color.dark_red())
        await ctx.channel.send(embed=emb)




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
