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

# Additional Requirements
import errorSupport

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
         'etime': 0,
         'erun': asyncio.Event(loop=bot.loop),
         }

if path.exists('persistence.private') and path.isfile('persistence.private'):
    with open('persistence.private', 'r') as file:
        state['persistent'] = json.load(file)
        print('Loaded persistent data')
else:
    with open('persistence.private', 'x') as file:
        json.dump(state['persistent'], file)


# Check Definitions
def is_admin():
    async def predicate(ctx):
        # Is the command user Kodikuu?
        c1 = ctx.author.id == 124207277174423552
        # Is the command user the current bot owner?
        c2 = ctx.author.id == bot.owner_id
        # Does the command user have the Jedi role?
        c3 = ctx.author.top_role.name == "Jedi"
        # Does the command user have the Parsec Team role?
        c4 = ctx.author.top_role.name == "Parsec Team"
        return c1 or c2 or c3 or c4
    return commands.check(predicate)


# Background Tasks

# Function + Event Definitions
@bot.event
async def on_message(message):
    # Return if bot message
    if message.author == bot.user:
        return

    # Anything that isn't a command goes inside this 'if' statement.
    if not (message.content.startswith(">") or bot.user in message.mentions):
        # Look for error codes if a command isn't used.
        if await eSupport.checkNums(message):
            return

        # Implement basic anti-spam

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use that command.")
    else:
        raise error


async def saveP():
    with open('persistence.private', 'w') as file:
        json.dump(state['persistent'], file)


@bot.command()
async def latency(ctx):
    val = round(bot.latency, 5)
    await ctx.send(f'Latency: {val}ms')


@bot.command(description='Restart the bot.')
@is_admin()
async def restart(ctx):
    await ctx.send('Restarting.')
    exit()


@bot.command(description='Shut down the bot.', hidden=True)
@is_admin()
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

# Initialise module classes
eSupport = errorSupport.eSupport(bot)
bot.add_cog(eSupport)

# Register tasks

# Start bot
print('Starting Bot')

bot.run(core['token'])

if state['state'] == 'shutdown':
    exit(0x78)
else:
    exit()
