from os import getenv, walk, remove, path, environ
from asyncio import run_coroutine_threadsafe
from time import sleep
import subprocess
import random

import discord
# from discord.ext import commands
from discord.utils import find
from dotenv import load_dotenv
from pytube import YouTube
#environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
# from moviepy.video.io.VideoFileClip import VideoFileClip
from requests.structures import CaseInsensitiveDict

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
HELP_MSG = getenv('HELP_MSG')
HELP_MSG_2 = getenv('HELP_MSG_2')
HELP_MSG_3 = getenv('HELP_MSG_3')
UNKNOWN_COMMAND_MSG = getenv('UNKNOWN_COMMAND_MSG')
MEME_ADD_SUCC_MSG = getenv('MEME_ADD_SUCC_MSG')
MEME_ADD_FAIL_MSG = getenv('MEME_ADD_FAIL_MSG')
REMOVE_MEME_MSG = getenv('REMOVE_MEME_MSG')
REMOVE_MEME_FAIL_MSG = getenv('REMOVE_MEME_FAIL_MSG')
SOUND_FILE_DIR = getenv('SOUND_FILE_DIR')
NO_MEMES_MSG = getenv('NO_MEMES_MSG')
NO_PERMISSION_MSG = getenv('NO_PERMISSION_MSG')
NO_CHANNEL_MSG = getenv('NO_CHANNEL_MSG')
MAX_LENGTH_SECONDS = int(getenv('MAX_LENGTH_SECONDS'))
MAX_DOWNLOAD_LEN_SECONDS = int(getenv('MAX_DOWNLOAD_LEN_SECONDS'))

MEME_ADD_FAIL_MSG_ARR = (MEME_ADD_FAIL_MSG.replace('0', str(MAX_LENGTH_SECONDS))
                            .split(','))

print("Bot started, env loaded.")

def add_meme(argv):
    try:
        name = argv[0]
        url = argv[1]

        if name in memes:
            print('Meme already exists')
            return (None, 0)

        # Scrape video file from youtube
        yt = YouTube(url)
        if yt.length > MAX_DOWNLOAD_LEN_SECONDS:
            print('Full video too long')
            return (None, 1)
        elif len(argv) == 3:
            start = argv[2]
            end = yt.length + 1

            start = sum(int(x) * 60 ** i
                    for i, x in enumerate(reversed(start.split(':'))))

            if end - start > MAX_LENGTH_SECONDS:
                print('Clip too long')
                return (None, 2)

            trim = True
        elif len(argv) > 3:
            start = argv[2]
            end = argv[3]

            start = sum(int(x) * 60 ** i
                    for i, x in enumerate(reversed(start.split(':'))))

            if end == '-':
                end = yt.length + 1
            else:
                end = sum(int(x) * 60 ** i
                    for i, x in enumerate(reversed(end.split(':'))))

            if end - start > MAX_LENGTH_SECONDS:
                print('Clip too long')
                return (None, 2)

            trim = True
        elif yt.length > MAX_LENGTH_SECONDS:
            print('Video too long')
            return (None, 2)
        else:
            trim = False

        # Download
        pref = name + '--'
        filepath = yt.streams.get_audio_only().download(
                    output_path=SOUND_FILE_DIR,
                    filename_prefix=pref)

        if trim:
            fn, ext = path.splitext(filepath)
            trimmed = fn + '-trim' + ext
            # Wait for file to download
            attempt = 0
            while not path.exists(filepath):
                sleep(0.25)
                attempt += 1
                if attempt > 40:
                    remove(filepath)
                    print('Timed out')
                    return (None, 3)

            ffmpeg_extract_subclip(filepath, start, end,
                    targetname=trimmed)
            # with VideoFileClip(filepath) as vid:
            #     clip = vid.subclip(start, end)
            #     clip.write_videofile(trimmed)

            remove(filepath)

            filepath = trimmed

        # Normalize volume
        command = ["ffmpeg-normalize", "-c:a", "aac", "-of", "soundfiles/",
                    "-q", "-f", filepath]
        subprocess.run(command, check=True)

        # Add to dictionary
        memes[name] = filepath
        return (name, None)

    except Exception as e:
        print(e)
        try:
            if path.exists(filepath):
                remove(filepath)
        except:
            pass
        return (None, 4)

def remove_meme(argv):
    try:
        name = argv[0]
        if name in memes:
            remove(memes[name])
            if path.exists(memes[name]):
                return None
            else:
                memes.pop(name)
                return name
        else:
            return None

    except Exception as e:
        print(e)
        return None

def keys_str(dict):
    s = ''
    for key in sorted(dict.keys(), key=str.casefold):
        s += key + ", "
    return s[:-2]

# bot = commands.Bot(command_prefix='!')
bot = discord.Bot(debug_guild=905274461962530817)

# Read sound file names into dictionary
memes = CaseInsensitiveDict()
try:
    _, _, filenames = next(walk(SOUND_FILE_DIR))
    for fn in filenames:
        cmd = fn.split('--')[0]
        memes[cmd] = SOUND_FILE_DIR + fn
except Exception:
    pass

@bot.command(name='mb')
async def memebot(ctx, cmd='help', *argv):

    def disconnect_after(error):
        sleep(1)
        coroutine = ctx.voice_client.disconnect()
        future = run_coroutine_threadsafe(coroutine, bot.loop)
        try:
            future.result()
        except:
            pass

        print('Played meme.')

    if cmd == 'help':
        # Send instructions on how to use Son of Memebot
        # There's a built in way to do help, look that up
        await ctx.send(HELP_MSG)
        await ctx.send(HELP_MSG_2)
        await ctx.send(HELP_MSG_3)
        print('Sent help message.')

    elif cmd == 'list':
        # Send a list of available memes
        if len(memes) > 0:
            await ctx.send(keys_str(memes))
        else:
            await ctx.send(NO_MEMES_MSG)

        print('Sent list.')

    elif cmd == 'add':
        newcmd, errorcode = add_meme(argv)

        if newcmd is None:
            await ctx.send(MEME_ADD_FAIL_MSG_ARR[errorcode])
            print('Failed to add meme, code {}.'.format(errorcode))
        else:
            succ_msg = MEME_ADD_SUCC_MSG + ' ' + newcmd
            await ctx.send(succ_msg)
            print('Added meme: {}'.format(newcmd))

    elif cmd == 'remove':
        admin = find(lambda r: r.name == 'Admin', ctx.guild.roles)
        mod = find(lambda r: r.name == 'Mod', ctx.guild.roles)

        # if admin in ctx.author.roles or mod in ctx.author.roles:
        # Remove a meme
        rmvd = remove_meme(argv)

        if rmvd is None:
            await ctx.send(REMOVE_MEME_FAIL_MSG)
            print('Failed to remove meme.')
        else:
            rm_msg = REMOVE_MEME_MSG + ' ' + rmvd
            await ctx.send(rm_msg)
            print('Removed meme: {}'.format(rmvd))
        # else:
        #     await ctx.send(NO_PERMISSION_MSG)

    elif cmd == 'random' or cmd in memes:
        channel = ctx.author.voice.channel

        if channel:
            if ctx.voice_client is None:
                if cmd == 'random':
                    audio_fn = random.choice(list(memes.values()))
                else:
                    audio_fn = memes[cmd]

                await channel.connect()
                ctx.voice_client.play(discord.FFmpegPCMAudio(audio_fn),
                        after=disconnect_after)
        else:
            await ctx.send(NO_CHANNEL_MSG)
            print('User not in voice channel.')

    else:
        await ctx.send(UNKNOWN_COMMAND_MSG)

bot.run(TOKEN)
