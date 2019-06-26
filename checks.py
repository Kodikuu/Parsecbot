from discord.ext import commands


def trusted():
    async def predicate(ctx):
        # Is the command user trusted?
        role = ["Jedi", "Moderator", "Parsec Team"]
        return any([x in [y.name for y in ctx.author.roles] for x in role])
    return commands.check(predicate)


def moderator():
    async def predicate(ctx):
        # Is the command user trusted?
        role = ["Moderator", "Parsec Team"]
        return any([x in [y.name for y in ctx.author.roles] for x in role])
    return commands.check(predicate)


def green():
    async def predicate(ctx):
        # Is the command user trusted?
        role = ["Hero", "Jedi", "Moderator", "Parsec Team"]
        return any([x in [y.name for y in ctx.author.roles] for x in role])
    return commands.check(predicate)


def admin():
    async def predicate(ctx):
        c1 = await ctx.bot.is_owner(ctx.author)
        c2 = ctx.author.id in [275729136876519426, 206566115466280960]
        return c1 or c2
    return commands.check(predicate)


def botsetup():
    async def predicate(ctx):
        return ctx.channel.name.lower() == "bot-setup"
    return commands.check(predicate)
