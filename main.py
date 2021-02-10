"""
Created by Epic at 9/5/20
"""
from speedcord import Client
from speedian.command_handler import CommandHandler
from logging import basicConfig, DEBUG
from os import environ as env
from pymongo import MongoClient

basicConfig(level=DEBUG)

client = Client(1536, env["TOKEN"])
mongo = MongoClient(env.get("MONGO_URI"))
client.db = mongo["news-bot"]
commands = CommandHandler(client, env["CLIENT_ID"], guild_id=env.get("DEBUG_GUILD"))
commands.load_extension("discover")
commands.load_extension("management")

client.run()


