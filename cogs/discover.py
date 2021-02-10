from speedian.types import Cog, CommandContext, ChannelType
from speedian.annotations import command, option
from speedcord.http import Route
from asyncio import sleep
from os import environ as env
from urllib.parse import quote as uriencode

contexts = []


class SearchContext:
    def __init__(self, ctx: CommandContext, search_results, author):
        self.ctx = ctx
        self.results = search_results
        self.active_page = 0
        self.ctx.client.loop.create_task(self.expire_timer())
        self.message_id = None
        self.author = author
        self.expired = False

    async def expire_timer(self):
        await sleep(2 * 60)
        await self.expire()

    async def expire(self):
        if self.expired:
            return
        self.expired = True
        r = Route("DELETE", "/channels/{channel_id}/messages/{message_id}", channel_id=self.ctx.message.channel_id,
                  message_id=self.message_id)
        await self.ctx.client.http.request(r)
        contexts.remove(self)

    def get_page(self):
        try:
            page = self.results[self.active_page]
        except IndexError:
            return {
                "title": "N/A",
                "description": "There is nothing on this page. Just darkness",
                "color": 0x00FFFF,
                "footer": {
                    "text": "Page %s/%s | Press the heart to add" % (self.active_page + 1, len(self.results))
                }
            }
        return {
            "title": page["name"].replace("-", " ").title(),
            "description": page["description"],
            "color": 0x00FFFF,
            "footer": {
                "text": "Page %s/%s | Press the heart to add" % (self.active_page + 1, len(self.results))
            }
        }

    async def send_initial(self):
        await self.ctx.send(embed=self.get_page())

    async def update(self):
        r = Route("PATCH", "/channels/{channel_id}/messages/{message_id}", channel_id=self.ctx.message.channel_id,
                  message_id=self.message_id)
        await self.ctx.client.http.request(r, json={
            "embed": self.get_page()
        })

    async def initial_callback(self, message_id):
        self.message_id = message_id
        await self.add_reaction("%E2%97%80%EF%B8%8F")  # Left arrow
        await self.add_reaction("%E2%9D%A4%EF%B8%8F")  # Heart
        await self.add_reaction("%E2%9E%A1%EF%B8%8F")  # Right arrow

    async def add_reaction(self, reaction):
        r = Route("PUT", "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
                  channel_id=self.ctx.message.channel_id, message_id=self.message_id, emoji=reaction)
        await self.ctx.client.http.request(r)

    async def remove_reaction(self, reaction):
        r = Route("DELETE", "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{user_id}",
                  channel_id=self.ctx.message.channel_id, message_id=self.message_id, emoji=reaction,
                  user_id=self.author)
        await self.ctx.client.http.request(r)

    async def on_reaction(self, data):
        emoji = uriencode(data["emoji"]["name"])
        if emoji == "%E2%97%80%EF%B8%8F":
            self.active_page -= 1
            await self.update()
            await self.remove_reaction("%E2%97%80%EF%B8%8F")
        elif emoji == "%E2%9D%A4%EF%B8%8F":
            if (int(self.ctx.message.member["permissions"]) & 0x20000000) != 0x20000000:
                await self.ctx.send(f"<@{self.author}> Uh oh, you need manage webhooks permissions to add news!")
                return
            try:
                page = self.results[self.active_page]
            except IndexError:
                await self.ctx.send(f"<@{self.author}> Uh oh, theres no channel selected here."
                                    " Select a channel and press the heart to add it!")
                return
            await self.expire()

            r = Route("POST", "/channels/{news_channel_id}/followers", news_channel_id=page["_id"])
            await self.ctx.client.http.request(r, json={
                "webhook_channel_id": self.ctx.message.channel_id
            })
        elif emoji == "%E2%9E%A1%EF%B8%8F":
            self.active_page += 1
            await self.update()
            await self.remove_reaction("%E2%9E%A1%EF%B8%8F")


class Discover(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.client.event_dispatcher.register("MESSAGE_CREATE", self.receive_message_ids)
        self.client.event_dispatcher.register("MESSAGE_REACTION_ADD", self.on_reaction)

    async def receive_message_ids(self, data, _):
        if data["author"]["id"] == env["CLIENT_ID"]:
            for context in contexts:
                if context.message_id is not None:
                    continue
                if context.ctx.message.channel_id == data["channel_id"]:
                    await context.initial_callback(data["id"])

    async def on_reaction(self, data, _):
        if data["user_id"] == env["CLIENT_ID"] or data["emoji"]["id"] is not None:
            return
        for context in contexts:
            if data["user_id"] == context.author and data["message_id"] == context.message_id:
                await context.on_reaction(data)

    @command(description="Search and find news!")
    @option("query", str, description="What to search for")
    async def search(self, ctx: CommandContext, query):
        search_results = list(self.client.db.channels.find({"$text": {"$search": query}}))
        if len(search_results) == 0:
            await ctx.send("Huh, it doesn't exist yet? Be the first to make it!")
            return
        context = SearchContext(ctx, search_results, ctx.message.member["user"]["id"])
        contexts.append(context)
        await context.send_initial()

    @command(description="Lists all news channel for you to browse through")
    @option("page", int, description="Jump to a specific page", required=False)
    async def list(self, ctx, page: int = 0):
        results = list(self.client.db.channels.find())
        context = SearchContext(ctx, results, ctx.message.member["user"]["id"])
        context.active_page = page
        contexts.append(context)
        await context.send_initial()

