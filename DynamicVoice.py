from discord.ext import commands
from discord import utils, errors
import checks


class DynamicVoice(commands.Cog):
    """
    A stateless cog that manages voice channels.
    It only has one command; >refresh, to manually make it check channels
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        await self.refresh()

    @commands.command()
    @checks.trusted()
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
            name = f"{limit} Players"

            if limit == 0:
                createText = "DynamicVoice - No empty Unlimited Player channel"
                name = "Unlimited Players"

            empty = []
            for channel in cList:
                if not channel.members:
                    empty.append(channel)

            if not empty:
                await guild.create_voice_channel(name,
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
