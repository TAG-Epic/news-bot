"""
Created by Epic at 9/5/20
"""
from speedcord import Client
from speedian.command_handler import CommandHandler
from logging import basicConfig, DEBUG
from os import environ as env
from elasticsearch import AsyncElasticsearch

basicConfig(level=DEBUG)

client = Client(1536, env["TOKEN"])
client.elastic = AsyncElasticsearch(hosts=("localhost", "elastic")[bool(env.get("PROD_ENV"))])

commands = CommandHandler(client, env["CLIENT_ID"], guild_id=env.get("DEBUG_GUILD"))
commands.load_extension("discover")
commands.load_extension("manage")
commands.load_extension("utils")


async def setup():
    await client.elastic.indices.create("channels", ignore=400)

client.loop.create_task(setup())
client.run()
