from speedian.types import Cog, CommandContext, ChannelType
from speedian.annotations import command, option
from speedcord.http import Route


class Manage(Cog):
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

        if (await self.client.elastic.get(index="channels", id=channel, ignore=404))["found"]:
            return await ctx.send("Already submitted. Delete it with /delete")
        await self.client.elastic.index(index="channels", id=channel,
                                        body={"id": channel, "name": res["name"], "description": description})
        await self.client.elastic.indices.refresh(index="channels")
        await ctx.send("Listing created!")

    @command(description="Unlist your news channel")
    @option("channel", ChannelType, description="Channel to un-list")
    async def unlist(self, ctx, channel):
        if (int(ctx.message.member["permissions"]) & 0x20000000) != 0x20000000:
            return await ctx.send("You need manage webhooks to use this command!")

        if not (await self.client.elastic.get(index="channels", id=channel, ignore=404))["found"]:
            return await ctx.send("This channel is not listed yet. List it with /publish")
        await self.client.elastic.delete(index="channels", id=channel)
        await ctx.send("Listing deleted!")
