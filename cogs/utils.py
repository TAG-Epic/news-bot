from speedian.types import Cog, CommandContext
from speedian.annotations import command


class Utils(Cog):
    @command(description="Get links to the bot")
    async def invite(self, ctx: CommandContext):
        await ctx.send("Bot invite: <https://vote.rip/news-invite>\nSupport server: <https://vote.rip/news-support>")
