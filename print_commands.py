import requests
import json
from os import getenv
from sys import argv
from dotenv import load_dotenv

if len(argv) > 1:
    if argv[1] == "help":
        print("Use: python print_commands.py [guild_id (optional)]")
        exit()
    else:
        guild_id = argv[1]
else:
    guild_id = 0

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
APP_ID = getenv('APPLICATION_ID')

if guild_id:
    url = "https://discord.com/api/v8/applications/{}/guilds/{}/commands".format(APP_ID, guild_id)
else:
    url = "https://discord.com/api/v8/applications/{}/commands".format(APP_ID)

# For authorization, use bot token
headers = {
    "Authorization": "Bot {}".format(TOKEN)
}

cmds = requests.get(url, headers=headers)

byte_arr = b""
for cmd in cmds:
    byte_arr += cmd

cmds_arr = json.loads(byte_arr.decode("utf-8"))
