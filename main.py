# Core Requirements
from discord.ext import commands
from discord import Activity, ActivityType, AppInfo
import asyncio

# Uncomment this with a full IDE, it should warn that it's not in use
# The idea being that we never import EVERYTHING. We don't need it all
# import discord

# File IO (Cryptographically Insecure)
import json
from os import path

# Timers
import time
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
         }

if path.exists('persistence.private') and path.isfile('persistence.private'):
    with open('persistence.private', 'r') as file:
        state['persistent'] = json.load(file)
        print('Loaded persistent data')
else:
    with open('persistence.private', 'x') as file:
        json.dump(state['persistent'], file)


# Function + Event Definitions

async def errorScrape(url = "https://support.parsecgaming.com/hc/en-us/sections/115000849851-Error-Codes"):
    r = requests.get(url)

    data = []
    for item in r.iter_lines():
        if "Error Codes - " in str(item):
            data.append(str(item))

    errorlist = []
    for item in data:
        tl = {}
        tmp = item.split(">")[1].split("<")[0].replace("&#39;", "'")

        tl['url'] = "https://support.parsecgaming.com" + item.split("\"")[1][:31]
        tl['title'] = tmp
        tl['desc'] = tmp[len(tmp.split("(")[0])+1:-1]
        tl['code'] = [word for word in tmp.split("(")[0].split() if word.isdigit()]

        errorlist.append(tl)
        state['elist'] = errorlist


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
