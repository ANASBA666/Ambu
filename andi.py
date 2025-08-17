import requests
import asyncio
import discord
from discord.ext import commands
import shutil
import os
import sys

# ANSI Colors for console output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"

# Static ASCII Art
ASCII_ART = f"""
{Colors.RED}
 ░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓███████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  
{Colors.RESET}
"""

# Token validation for user account
def validate_token(token):
    headers = {"Authorization": token}
    response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
    if response.status_code != 200:
        print(f"{Colors.RED}Invalid user token.{Colors.RESET}")
        sys.exit()
    user = response.json()
    print(f"{Colors.GREEN}Token valid for {user['username']}#{user['discriminator']}{Colors.RESET}")

# FFmpeg check
def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        print(f"{Colors.RED}FFmpeg not found. Install it from https://ffmpeg.org{Colors.RESET}")
        sys.exit()

# Load Opus library
def load_opus():
    try:
        if not discord.opus.is_loaded():
            discord.opus.load_opus("/data/data/com.termux/files/usr/lib/libopus.so")
            print(f"{Colors.GREEN}Opus library loaded successfully.{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Failed to load Opus library: {str(e)}{Colors.RESET}")
        sys.exit()

# Initialize bot with intents (self-bot mode)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", self_bot=True)

# Global variables
current_vc = None
audio_source = None
FFMPEG_OPTS = {
    'options': '-vn -af "volume=31dB,bass=g=51,highpass=f=100,lowpass=f=8000,compand=attacks=0:decays=0:points=-80/-80|-40/-20|0/0,aloop=loop=-1:size=2e+09"',
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
        print(f"{Colors.RED}File {new_file} doesn’t exist.{Colors.RESET}")
        return False
    try:
        new_audio = discord.FFmpegPCMAudio(new_file, **FFMPEG_OPTS)
        if current_vc and current_vc.is_connected():
            if current_vc.is_playing():
                current_vc.stop()
            current_vc.play(new_audio)
            print(f"{Colors.GREEN}Switched to playing {new_file} in 🔊 {current_vc.channel.name}{Colors.RESET}")
            audio_source = new_audio
            return True
        else:
            print(f"{Colors.RED}Bot isn’t in a voice channel.{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}Failed to change audio to {new_file}: {str(e)}{Colors.RESET}")
        return False

@bot.event
async def on_ready():
    print(ASCII_ART)
    print(f"{Colors.CYAN}Logged in as {bot.user} - Ready to operate{Colors.RESET}")

    servers = list(bot.guilds)
    if not servers:
        print(f"{Colors.RED}Not in any servers.{Colors.RESET}")
        await bot.close()
        return

    # Server selection
    print(f"\n{Colors.MAGENTA}=== SERVER SELECTION ==={Colors.RESET}")
    print(f"{Colors.YELLOW}Select a server by entering its number:{Colors.RESET}")
    for i, server in enumerate(servers):
        print(f"{Colors.CYAN}{i + 1}. 🏰 {server.name}{Colors.RESET}")
    print(f"{Colors.MAGENTA}========================={Colors.RESET}\n")

    while True:
        try:
            server_choice = int(input(f"{Colors.YELLOW}Enter server number: {Colors.RESET}")) - 1
            if server_choice < 0 or server_choice >= len(servers):
                raise ValueError("Invalid server number.")
            break
        except ValueError:
            print(f"{Colors.RED}Invalid input. Try again.{Colors.RESET}")

    guild = servers[server_choice]
    print(f"\n{Colors.GREEN}Selected server: 🏰 {guild.name}{Colors.RESET}\n")

    # Voice channel selection
    voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
    if not voice_channels:
        print(f"{Colors.RED}No voice channels found in this server.{Colors.RESET}")
        await bot.close()
        return

    print(f"\n{Colors.MAGENTA}=== VOICE CHANNEL SELECTION ==={Colors.RESET}")
    print(f"{Colors.YELLOW}Select a voice channel by entering its number:{Colors.RESET}")
    for i, channel in enumerate(voice_channels):
        user_limit = channel.user_limit if channel.user_limit > 0 else "∞"
        print(f"{Colors.CYAN}{i + 1}. 🔊 {channel.name} (Users: {len(channel.members)}/{user_limit}) {Colors.RESET}")
    print(f"{Colors.MAGENTA}==============================={Colors.RESET}\n")

    while True:
        try:
            channel_choice = int(input(f"{Colors.YELLOW}Enter voice channel number: {Colors.RESET}")) - 1
            if channel_choice < 0 or channel_choice >= len(voice_channels):
                raise ValueError("Invalid voice channel number.")
            break
        except ValueError:
            print(f"{Colors.RED}Invalid input. Try again.{Colors.RESET}")

    voice_channel = voice_channels[channel_choice]
    print(f"\n{Colors.GREEN}Joining voice channel: 🔊 {voice_channel.name}{Colors.RESET}\n")

    # Connect to voice channel
    retries = 3
    for attempt in range(retries):
        try:
            global current_vc
            current_vc = await voice_channel.connect()
            print(f"{Colors.GREEN}Successfully connected to 🔊 {voice_channel.name}{Colors.RESET}\n")
            break
        except asyncio.TimeoutError:
            print(f"{Colors.RED}Attempt {attempt + 1}/{retries}: Timeout while connecting. Retrying...{Colors.RESET}")
        except discord.Forbidden:
            print(f"{Colors.RED}Lacks permission to join or speak in this channel.{Colors.RESET}")
            await bot.close()
            return
        except Exception as e:
            print(f"{Colors.RED}Failed to connect to 🔊 {voice_channel.name}: {str(e)}{Colors.RESET}")
            if attempt == retries - 1:
                await bot.close()
                return
    else:
        print(f"{Colors.RED}Failed to connect after {retries} attempts. Exiting...{Colors.RESET}")
        await bot.close()
        return

    # Play audio
    media_url = os.path.abspath("test.mp4")
    print(f"{Colors.YELLOW}Using file: {media_url}{Colors.RESET}")

    try:
        global audio_source
        audio_source = discord.FFmpegPCMAudio(media_url, **FFMPEG_OPTS)
        current_vc.play(audio_source)
        print(f"{Colors.GREEN}Playing {media_url} in 🔊 {voice_channel.name} - Looping{Colors.RESET}\n")
        while True:
            await asyncio.sleep(5)
            if current_vc.channel != voice_channel:
                print(f"{Colors.YELLOW}Moved to 🔊 {current_vc.channel.name}{Colors.RESET}")
                voice_channel = current_vc.channel
    except discord.ClientException as e:
        print(f"{Colors.RED}Discord client error: {str(e)}{Colors.RESET}")
        await murder_audio()
    except Exception as e:
        print(f"{Colors.RED}FFmpeg error: {str(e)}{Colors.RESET}")
        await murder_audio()
    finally:
        await murder_audio()

@bot.event
async def on_message(message):
    if not isinstance(message.channel, discord.DMChannel):
        return
    print(f"{Colors.YELLOW}DM from {message.author}: {message.content}{Colors.RESET}")
    await bot.process_commands(message)

@bot.command()
async def switch(ctx, channel_id: int):
    try:
        target_channel = bot.get_channel(channel_id)
        if not target_channel:
            print(f"{Colors.RED}Channel {channel_id} doesn’t exist.{Colors.RESET}")
            await ctx.message.add_reaction('❌')
            return
        if not isinstance(target_channel, discord.VoiceChannel):
            print(f"{Colors.RED}Channel {channel_id} isn’t a voice channel.{Colors.RESET}")
            await ctx.message.add_reaction('❌')
            return
        guild = target_channel.guild
        if guild not in bot.guilds:
            print(f"{Colors.RED}Not in guild {guild.name}.{Colors.RESET}")
            await ctx.message.add_reaction('❌')
            return

        global current_vc, audio_source
        if current_vc and current_vc.is_playing():
            print(f"{Colors.YELLOW}Saving current audio state.{Colors.RESET}")
            audio_source = discord.FFmpegPCMAudio("test.mp4", **FFMPEG_OPTS)

        await murder_audio()
        print(f"{Colors.YELLOW}Connecting to 🔊 {target_channel.name}{Colors.RESET}")

        retries = 3
        for attempt in range(retries):
            try:
                current_vc = await target_channel.connect()
                print(f"{Colors.GREEN}Switched to 🔊 {target_channel.name}{Colors.RESET}")
                current_vc.play(audio_source or discord.FFmpegPCMAudio("test.mp4", **FFMPEG_OPTS))
                await ctx.message.add_reaction('✅')
                return
            except asyncio.TimeoutError:
                print(f"{Colors.RED}Attempt {attempt + 1}/{retries}: Timeout switching to {target_channel.name}. Retrying...{Colors.RESET}")
            except discord.Forbidden:
                print(f"{Colors.RED}No permission to join or speak in {target_channel.name}.{Colors.RESET}")
                await ctx.message.add_reaction('❌')
                return
            except Exception as e:
                print(f"{Colors.RED}Switch failed for {target_channel.name}: {str(e)}{Colors.RESET}")
                if attempt == retries - 1:
                    await ctx.message.add_reaction('💥')
                    return
    except ValueError:
        print(f"{Colors.RED}Invalid channel ID format.{Colors.RESET}")
        await ctx.message.add_reaction('❌')
    except Exception as e:
        print(f"{Colors.RED}Switch command error: {str(e)}{Colors.RESET}")
        await ctx.message.add_reaction('💥')

@bot.command()
async def change(ctx, new_file: str):
    print(f"{Colors.YELLOW}DM from {ctx.author}: !change {new_file}{Colors.RESET}")
    try:
        if await change_audio(new_file):
            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❌')
    except Exception as e:
        print(f"{Colors.RED}Change command error: {str(e)}{Colors.RESET}")
        await ctx.message.add_reaction('💥')

if __name__ == "__main__":
    print(ASCII_ART)
    check_ffmpeg()
    load_opus()
    token = "MTIwMTkwNDY4NjE0ODM2MjM3MQ.GhSrxE.kAnmorH8HAoifGjdcsUDCu8OmIpZibn4Qrl-7A"  # Replace with your user token
    validate_token(token)
    bot.run(token)
