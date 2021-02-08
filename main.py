"""
Created by Epic at 9/5/20
"""

import speedcord
from speedcord.http import Route
from os import environ as env
from logging import basicConfig, DEBUG

client = speedcord.Client(intents=512)
basicConfig(level=DEBUG)

client.token = env["TOKEN"]
client.run()
