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
async def errorScrape():
    url = "https://support.parsecgaming.com/hc/en-us/sections/115000849851"
    while True:
        await state['erun'].wait()  # Wait until triggered

        if state['etime'] > time() - 60:
            state['erun'].unset()
            return  # Don't repeat more than once a minute

        r = requests.get(url)

        data = []
        for item in r.iter_lines():
            if "Error Codes - " in str(item):
                data.append(str(item))

        errorlist = []
        for item in data:
            tl = {}

            v = "https://support.parsecgaming.com" + item.split("\"")[1][:31]
            tl['url'] = v

            tmp = item.split(">")[1].split("<")[0].replace("&#39;", "'")

            v = [word for word in tmp.split("(")[0].split() if word.isdigit()]
            tl['code'] = v

            tl['title'] = tmp
            tl['desc'] = tmp[len(tmp.split("(")[0])+1:-1]

            errorlist.append(tl)
            state['elist'] = errorlist

        state['erun'].clear()


# Function + Event Definitions
@bot.event
async def on_message(message):
    # Return if bot message
    if message.author == bot.user:
        return

    # Anything that isn't a command goes inside this 'if' statement.
    if not (message.content.startswith(">") or bot.user in message.mentions):
        # Look for error codes if a command isn't used.
        tmp = message.content.split()
        for i in tmp:
            if i.isdigit() or i in state['persistent']['errors'].keys():
                # If any 'word' in the message is a number, or a manual error.
                state['erun'].set()
                await errorProcess(message, i, False)
                return

        # Look for error phrases if a command isn't used.
        for code in state['persistent']['errors'].keys():
            if code.lower() in message.content.lower():
                state['erun'].set()
                await errorProcess(message, code, False)
                return

        # Implement basic anti-spam

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use that command.")


async def saveP():
    with open('persistence.private', 'w') as file:
        json.dump(state['persistent'], file)


@bot.command()
async def error(ctx, errorcode):
    # Just makes things easier when running errorprocess not as a command.
    state['erun'].set()
    await errorProcess(ctx, errorcode, True)


@bot.command()
@is_admin()
async def scrape(ctx):
    state['etime'] = 0
    state['erun'].set()


async def errorProcess(ctx, ecode, explicit=False):
    # Get scraped error
    error = None
    for e in state['elist']:
        if error is not None:
            break
        for code in e['code']:
            if ecode == code:
                error = e
                # Correct error with persistent modifications.
                if ecode in state["persistent"]["errors"].keys():
                    for key in state["persistent"]["errors"][ecode].keys():
                        error[key] = state["persistent"]["errors"][ecode][key]
                break
    else:
        # Search through persistence data for manually added key
        if ecode in state["persistent"]["errors"].keys():
            error = state["persistent"]["errors"][ecode]

        else:
            if explicit:
                desc = "Please contact staff or correct your error code."
                emb = Embed(title=f"{ecode}: Not Documented.",
                            description=desc,
                            timestamp=datetime.datetime.now(),
                            color=Color.dark_red())
                await ctx.channel.send(embed=emb)
            return  # No error found

    # Ensure error is complete, input placeholders if not
    for key in ["title", "desc", "url"]:
        if key not in error.keys():
            error[key] = ""

    await errorResponse(ctx, error, explicit)


async def errorResponse(ctx, error, explicit=False):
    def check(reaction, user):
        e = str(reaction.emoji)
        return e == '❎' or e == '✅' and not user == bot.user

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
@is_admin()
async def erroredit(ctx, code, key, *desc):
    if "errors" not in state["persistent"].keys():
        state["persistent"]["errors"] = {}

    if key not in ["title", "url", "desc", "remove"]:
        ctx.send("Invalid key to edit")

    if code not in state["persistent"]["errors"].keys():
        state["persistent"]["errors"][code] = {}

    if key == "remove":
        del state["persistent"]["errors"][code]
    else:
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

# Register tasks
bot.loop.create_task(errorScrape())

# Start bot
print('Starting Bot')

bot.run(core['token'])

if state['state'] == 'shutdown':
    exit(0x78)
else:
    exit()
