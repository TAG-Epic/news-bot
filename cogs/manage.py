from speedian.types import Cog, CommandContext, ChannelType
from speedian.annotations import command, option
from speedcord.http import Route


class Discover(Cog):

    @command(description="Adds a channel to the listings")
    @option("channel", ChannelType, description="The channel to list")
    @option("description", str, description="The description to be listed")
    async def publish(self, ctx: CommandContext, channel, description):
        if (int(ctx.message.member["permissions"]) & 0x20000000) != 0x20000000:
            return await ctx.send("You need manage webhooks to use this command!")

        r = Route("GET", "/channels/{news_channel_id}", news_channel_id=channel)
        res = await (await self.client.http.request(r)).json()
        if res["type"] != 5:
            return await ctx.send("You can only submit news channels!")
        if self.client.db.channels.find_one({"_id": res["id"]}) is not None:
            return await ctx.send("Already submitted. Delete it with /delete")
        self.client.db.channels.insert_one({"_id": res["id"], "name": res["name"], "description": res["description"]})
        await ctx.send("Listing created!")
