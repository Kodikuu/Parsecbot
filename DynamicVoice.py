from discord.ext import commands
from discord import utils, errors


class DynamicVoice(commands.Cog):
    """
    A stateless cog that manages voice channels.
    It only has one command; >refresh, to manually make it check channels
    """

    def __init__(self, bot):
        self.bot = bot

    def is_admin():
        async def predicate(ctx):
            # Is the command user Kodikuu?
            c1 = ctx.author.id == 124207277174423552
            # Is the command user the current bot owner?
            c2 = await ctx.bot.is_owner(ctx.author)
            # Does the command user have the Jedi role?
            c3 = ctx.author.top_role.name == "Jedi"
            # Does the command user have the Parsec Team role?
            c4 = ctx.author.top_role.name == "Admin"
            c5 = ctx.author.top_role.name == "Parsec Team"
            c6 = ctx.author.top_role.name == "Dark Side"
            c7 = ctx.author.top_role.name == "Engineering"
            return c1 or c2 or c3 or c4 or c5 or c6 or c7
        return commands.check(predicate)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        await self.refresh()

    @commands.command()
    @is_admin()
    async def refreshVoice(self, ctx):
        await self.refresh()

    async def refresh(self):
        Channels = {0: [],
                    2: [],
                    3: [],
                    4: []}

        # The only result for this get command should be the category.
        category = utils.get(self.bot.get_all_channels(),
                             name='Party Finder Voice')
        guild = category.guild

        # Sort channels.
        for channel in category.channels:
            Channels[channel.user_limit].append(channel)

        for limit in Channels.keys():
            cList = Channels[limit]

            position = Channels[limit][0].position
            createText = f"DynamicVoice - No empty {limit} Player channel"
            deleteText = "DynamicVoice - Too many Channels"

            if not limit:
                createText = "DynamicVoice - No empty Unlimited Player channel"

            empty = []
            for channel in cList:
                if not channel.members:
                    empty.append(channel)

            if not empty:
                await guild.create_voice_channel(f"{limit} Players",
                                                 category=category,
                                                 user_limit=limit,
                                                 position=position,
                                                 reason=createText)

            for channel in empty[1:]:
                try:
                    await channel.delete(reason=deleteText)

                except errors.NotFound:
                    # This error is fine
                    pass
                else:
                    raise
