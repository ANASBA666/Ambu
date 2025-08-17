import asyncio
import discord
from discord.ext import commands
import shutil
import os
import sys
import aiohttp

# ANSI Colors for console output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"

# Minimal ASCII Art for faster load
ASCII_ART = f"{Colors.RED}=== AUDIO BOT ==={Colors.RESET}"

# Token validation (async)
async def validate_token(token):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://discord.com/api/v9/users/@me", headers={"Authorization": token}) as response:
            if response.status != 200:
                print(f"{Colors.RED}Invalid token.{Colors.RESET}")
                sys.exit()
            user = await response.json()
            print(f"{Colors.GREEN}Logged as {user['username']}#{user['discriminator']}{Colors.RESET}")

# FFmpeg check
def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        print(f"{Colors.RED}FFmpeg missing. Get it: https://ffmpeg.org{Colors.RESET}")
        sys.exit()

# Load Opus library
def load_opus():
    try:
        if not discord.opus.is_loaded():
            discord.opus.load_opus("/data/data/com.termux/files/usr/lib/libopus.so")
    except Exception as e:
        print(f"{Colors.RED}Opus load failed: {e}{Colors.RESET}")
        sys.exit()

# Initialize bot
intents = discord.Intents(guilds=True, message_content=True, voice_states=True)
bot = commands.Bot(command_prefix="!", self_bot=True, intents=intents)

# Global variables
current_vc = None
audio_source = None
FFMPEG_OPTS = {
    'options': '-vn -af "volume=31dB,bass=g=51,highpass=f=100,lowpass=f=8000,compand=attacks=0:decays=0:points=-80/-80|-40/-20|0/0,aloop=loop=-1:size=2e+09"'
}

# Disconnect and stop audio
async def murder_audio():
    global current_vc, audio_source
    if current_vc:
        if current_vc.is_playing():
            current_vc.stop()
        await current_vc.disconnect()
        current_vc = None
    audio_source = None

# Change audio file
async def change_audio(new_file):
    global current_vc, audio_source
    if not os.path.exists(new_file):
        print(f"{Colors.RED}File {new_file} missing.{Colors.RESET}")
        return False
    try:
        new_audio = discord.FFmpegPCMAudio(new_file, **FFMPEG_OPTS)
        if current_vc and current_vc.is_connected():
            if current_vc.is_playing():
                current_vc.stop()
            current_vc.play(new_audio)
            print(f"{Colors.GREEN}Playing {new_file} in {current_vc.channel.name}{Colors.RESET}")
            audio_source = new_audio
            return True
        print(f"{Colors.RED}Not in voice channel.{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.RED}Audio switch failed: {e}{Colors.RESET}")
        return False

@bot.event
async def on_ready():
    print(ASCII_ART)
    servers = list(bot.guilds)
    if not servers:
        print(f"{Colors.RED}No servers found.{Colors.RESET}")
        await bot.close()
        return

    # Fast server selection
    print(f"{Colors.YELLOW}Servers:{Colors.RESET}")
    for i, server in enumerate(servers, 1):
        print(f"{i}. {server.name}")
    try:
        server_choice = int(input(f"{Colors.YELLOW}Pick server #: {Colors.RESET}")) - 1
        if server_choice < 0 or server_choice >= len(servers):
            raise ValueError
        guild = servers[server_choice]
        print(f"{Colors.GREEN}Selected: {guild.name}{Colors.RESET}")
    except ValueError:
        print(f"{Colors.RED}Invalid server choice.{Colors.RESET}")
        await bot.close()
        return

    # Fast voice channel selection
    voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
    if not voice_channels:
        print(f"{Colors.RED}No voice channels.{Colors.RESET}")
        await bot.close()
        return

    print(f"{Colors.YELLOW}Voice Channels:{Colors.RESET}")
    for i, channel in enumerate(voice_channels, 1):
        print(f"{i}. {channel.name}")
    try:
        channel_choice = int(input(f"{Colors.YELLOW}Pick channel #: {Colors.RESET}")) - 1
        if channel_choice < 0 or channel_choice >= len(voice_channels):
            raise ValueError
        voice_channel = voice_channels[channel_choice]
        print(f"{Colors.GREEN}Joining: {voice_channel.name}{Colors.RESET}")
    except ValueError:
        print(f"{Colors.RED}Invalid channel choice.{Colors.RESET}")
        await bot.close()
        return

    # Connect to voice channel
    global current_vc
    try:
        current_vc = await voice_channel.connect(timeout=10, reconnect=True)
        print(f"{Colors.GREEN}Connected to {voice_channel.name}{Colors.RESET}")
    except asyncio.TimeoutError:
        print(f"{Colors.RED}Connection timeout.{Colors.RESET}")
        await bot.close()
        return
    except discord.Forbidden:
        print(f"{Colors.RED}No permissions for {voice_channel.name}.{Colors.RESET}")
        await bot.close()
        return
    except Exception as e:
        print(f"{Colors.RED}Connection failed: {e}{Colors.RESET}")
        await bot.close()
        return

    # Play audio
    media_url = os.path.abspath("test.mp4")
    try:
        global audio_source
        audio_source = discord.FFmpegPCMAudio(media_url, **FFMPEG_OPTS)
        current_vc.play(audio_source)
        print(f"{Colors.GREEN}Playing {media_url} in {voice_channel.name}{Colors.RESET}")
        while True:
            await asyncio.sleep(5)
            if current_vc.channel != voice_channel:
                print(f"{Colors.YELLOW}Moved to {current_vc.channel.name}{Colors.RESET}")
                voice_channel = current_vc.channel
    except Exception as e:
        print(f"{Colors.RED}Playback error: {e}{Colors.RESET}")
        await murder_audio()
    finally:
        await murder_audio()

@bot.event
async def on_message(message):
    if not isinstance(message.channel, discord.DMChannel):
        return
    await bot.process_commands(message)

@bot.command()
async def switch(ctx, channel_id: int):
    try:
        target_channel = bot.get_channel(channel_id)
        if not target_channel or not isinstance(target_channel, discord.VoiceChannel):
            print(f"{Colors.RED}Invalid voice channel {channel_id}.{Colors.RESET}")
            await ctx.message.add_reaction('❌')
            return
        if target_channel.guild not in bot.guilds:
            print(f"{Colors.RED}Not in guild {target_channel.guild.name}.{Colors.RESET}")
            await ctx.message.add_reaction('❌')
            return

        global current_vc, audio_source
        if current_vc and current_vc.is_playing():
            audio_source = discord.FFmpegPCMAudio("test.mp4", **FFMPEG_OPTS)

        await murder_audio()
        try:
            current_vc = await target_channel.connect(timeout=10, reconnect=True)
            current_vc.play(audio_source or discord.FFmpegPCMAudio("test.mp4", **FFMPEG_OPTS))
            print(f"{Colors.GREEN}Switched to {target_channel.name}{Colors.RESET}")
            await ctx.message.add_reaction('✅')
        except asyncio.TimeoutError:
            print(f"{Colors.RED}Timeout switching to {target_channel.name}.{Colors.RESET}")
            await ctx.message.add_reaction('❌')
        except discord.Forbidden:
            print(f"{Colors.RED}No permissions for {target_channel.name}.{Colors.RESET}")
            await ctx.message.add_reaction('❌')
        except Exception as e:
            print(f"{Colors.RED}Switch failed: {e}{Colors.RESET}")
            await ctx.message.add_reaction('💥')
    except ValueError:
        print(f"{Colors.RED}Invalid channel ID.{Colors.RESET}")
        await ctx.message.add_reaction('❌')
    except Exception as e:
        print(f"{Colors.RED}Switch error: {e}{Colors.RESET}")
        await ctx.message.add_reaction('💥')

@bot.command()
async def change(ctx, new_file: str):
    try:
        if await change_audio(new_file):
            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❌')
    except Exception as e:
        print(f"{Colors.RED}Change error: {e}{Colors.RESET}")
        await ctx.message.add_reaction('💥')

async def main():
    check_ffmpeg()
    load_opus()
    token = "MTIwMTkwNDY4NjE0ODM2MjM3MQ.GhSrxE.kAnmorH8HAoifGjdcsUDCu8OmIpZibn4Qrl-7A"
    await validate_token(token)
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
