import requests
from os import getenv
from sys import argv
from dotenv import load_dotenv
import json

if len(argv) > 1 and argv[1] == "help":
    print("Use: python register_command.py [json path] [guild id]")
    exit()
elif len(argv) < 3:
    print("Requires both a command json file and a guild id")
    exit()
else:
    fn = argv[1]
    guild_id = argv[2]

# Read in command json file
try:
    with open(fn) as file:
        jcontent = json.load(file)
except Exception as e:
    print("Could not open file: {}".format(argv[1]))
    print(e)
    exit()

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
APP_ID = getenv('APPLICATION_ID')

url = "https://discord.com/api/v8/applications/{}/guilds/{}/commands".format(APP_ID, guild_id)

# For authorization, use bot token
headers = {
    "Authorization": "Bot {}".format(TOKEN)
}

r = requests.post(url, headers=headers, json=jcontent)

if "201" in r:
    print("Success")
elif "400" in r:
    print("POST failed")
else:
    print("Unknown response code.")
    print(r)
