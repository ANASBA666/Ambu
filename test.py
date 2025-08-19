

## Key Improveme
import requests
import asyncio
import discord
from discord.ext import commands
import traceback
import shutil
import os
import sys
import subprocess
import zipfile
import urllib.request
import platform

# ANSI Colors for clean console output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"

# Static ASCII Art - No animation, just shows up clean
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

# Audio style presets
AUDIO_STYLES = {
    'baby': {
        'options': '-vn -af "volume=20dB,bass=g=30,highpass=f=200,lowpass=f=4000,compand=attacks=0:decays=0:points=-80/-80|-40/-20|0/0,aloop=loop=-1:size=2e+09"',
        'description': 'Soft, gentle audio for babies'
    },
    'robot': {
        'options': '-vn -af "volume=25dB,bass=g=40,highpass=f=300,lowpass=f=6000,compand=attacks=0:decays=0:points=-80/-80|-40/-20|0/0,aloop=loop=-1:size=2e+09,aecho=0.8:0.5:60:0.3"',
        'description': 'Robotic, metallic sound with echo'
    },
    'scary': {
        'options': '-vn -af "volume=35dB,bass=g=60,highpass=f=150,lowpass=f=3000,compand=attacks=0:decays=0:points=-80/-80|-40/-20|0/0,aloop=loop=-1:size=2e+09,aecho=0.9:0.7:100:0.5"',
        'description': 'Dark, ominous audio with deep bass and echo'
    },
    'rage': {
        'options': '-vn -af "volume=40dB,bass=g=70,highpass=f=100,lowpass=f=8000,compand=attacks=0:decays=0:points=-80/-80|-40/-20|0/0,aloop=loop=-1:size=2e+09,aecho=0.6:0.4:50:0.3"',
        'description': 'Aggressive, powerful audio with maximum impact'
    },
    'normal': {
        'options': '-vn -af "volume=31dB,bass=g=51,highpass=f=100,lowpass=f=8000,compand=attacks=0:decays=0:points=-80/-80|-40/-20|0/0,aloop=loop=-1:size=2e+09"',
        'description': 'Standard audio settings'
    }
}

# Download and install FFmpeg automatically
def download_ffmpeg():
    system = platform.system().lower()
    if system == "windows":
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        ffmpeg_zip = "ffmpeg.zip"
        
        print(f"{Colors.YELLOW}Downloading FFmpeg for Windows...{Colors.RESET}")
        try:
            urllib.request.urlretrieve(ffmpeg_url, ffmpeg_zip)
            print(f"{Colors.GREEN}FFmpeg downloaded successfully!{Colors.RESET}")
            
            # Extract and install
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall("ffmpeg_temp")
            
            # Move ffmpeg.exe to current directory
            for root, dirs, files in os.walk("ffmpeg_temp"):
                for file in files:
                    if file == "ffmpeg.exe":
                        src_path = os.path.join(root, file)
                        shutil.copy2(src_path, "ffmpeg.exe")
                        print(f"{Colors.GREEN}FFmpeg installed successfully!{Colors.RESET}")
                        break
            
            # Cleanup
            shutil.rmtree("ffmpeg_temp")
            os.remove(ffmpeg_zip)
            
        except Exception as e:
            print(f"{Colors.RED}Failed to download FFmpeg: {str(e)}{Colors.RESET}")
            print(f"{Colors.YELLOW}Please download FFmpeg manually from https://ffmpeg.org{Colors.RESET}")
            return False
    else:
        print(f"{Colors.YELLOW}For non-Windows systems, please install FFmpeg manually{Colors.RESET}")
        return False
    return True

# Check and install FFmpeg if needed
def check_ffmpeg():
    if not shutil.which("ffmpeg") and not os.path.exists("ffmpeg.exe"):
        print(f"{Colors.YELLOW}FFmpeg not found. Attempting to download...{Colors.RESET}")
        if not download_ffmpeg():
            print(f"{Colors.RED}FFmpeg installation failed. Please install manually.{Colors.RESET}")
            sys.exit()
    else:
        print(f"{Colors.GREEN}FFmpeg found!{Colors.RESET}")

# Copy test.mp4 from Downloads
def setup_audio_file():
    downloads_path = os.path.expanduser("~/Downloads")
    source_file = os.path.join(downloads_path, "test.mp4")
    
    # If test.mp4 doesn't exist, look for any mp4 file
    if not os.path.exists(source_file):
        for file in os.listdir(downloads_path):
            if file.endswith('.mp4'):
                source_file = os.path.join(downloads_path, file)
                print(f"{Colors.YELLOW}Found audio file: {file}{Colors.RESET}")
                break
    
    if os.path.exists(source_file):
        # Copy to current directory
        shutil.copy2(source_file, "test.mp4")
        print(f"{Colors.GREEN}Audio file ready: test.mp4{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}No audio file found in Downloads folder!{Colors.RESET}")
        return False

# Token validation
def validate_token(token):
    headers = {"Authorization": token}
    response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
    if response.status_code != 200:
        print(f"{Colors.RED}Invalid token!{Colors.RESET}")
        sys.exit()
    user = response.json()
    print(f"{Colors.GREEN}Token valid for {user['username']}#{user['discriminator']}{Colors.RESET}")

# Load the Opus library
def load_opus():
    try:
        if not discord.opus.is_loaded():
            discord.opus.load_opus("/data/data/com.termux/files/usr/lib/libopus.so")
            print(f"{Colors.GREEN}Opus library loaded successfully.{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.YELLOW}Opus library not available, continuing without voice support{Colors.RESET}")

# Initialize bot
bot = commands.Bot(command_prefix="!", self_bot=True)

# Global variables
current_vc = None
audio_source = None
current_style = 'normal'
USER_ID = '1210402608070791230'  # Your Discord ID

# Stop audio
async def stop_audio():
    global current_vc, audio_source
    if current_vc:
        if current_vc.is_playing():
            current_vc.stop()
        await current_vc.disconnect()
        current_vc = None
    audio_source = None

# Change audio style
async def change_style(style_name):
    global current_style, current_vc, audio_source
    
    if style_name not in AUDIO_STYLES:
        return False, f"Unknown style: {style_name}"
    
    current_style = style_name
    style_config = AUDIO_STYLES[style_name]
    
    if current_vc and current_vc.is_connected():
        if current_vc.is_playing():
            current_vc.stop()
        
        new_audio = discord.FFmpegPCMAudio("test.mp4", options=style_config['options'])
        current_vc.play(new_audio)
        audio_source = new_audio
        
        return True, f"Switched to {style_name} style: {style_config['description']}"
    
    return False, "Not connected to voice channel"

# Change audio file
async def change_audio(new_file):
    global current_vc, audio_source
    if not os.path.exists(new_file):
        return False, f"File {new_file} doesn't exist"
    
    try:
        style_config = AUDIO_STYLES[current_style]
        new_audio = discord.FFmpegPCMAudio(new_file, options=style_config['options'])
        
        if current_vc and current_vc.is_connected():
            if current_vc.is_playing():
                current_vc.stop()
            current_vc.play(new_audio)
            audio_source = new_audio
            return True, f"Switched to {new_file} with {current_style} style"
        else:
            return False, "Not connected to voice channel"
    except Exception as e:
        return False, f"Failed to change audio: {str(e)}"

# Send available commands to user
async def send_commands():
    try:
        user = await bot.fetch_user(int(USER_ID))
        if user:
            embed = discord.Embed(
                title=" Audio Bot Commands",
                description="Available commands for controlling the audio bot:",
                color=0x00ff00
            )
            
            commands_text = """
** Basic Commands:**
`!switch <channel_id>` - Switch to different voice channel
`!stop` - Stop audio and disconnect
`!pause` - Pause audio
`!resume` - Resume audio

** Style Commands:**
`!style baby` - Soft, gentle audio
`!style robot` - Robotic, metallic sound
`!style scary` - Dark, ominous audio
`!style rage` - Aggressive, powerful audio
`!style normal` - Standard audio settings

** File Commands:**
`!change <filename>` - Change audio file
`!list` - List available audio files

**ℹ️ Info Commands:**
`!status` - Show current status
`!help` - Show this help message
            """
            
            embed.add_field(name="Commands", value=commands_text, inline=False)
            embed.add_field(name="Current Style", value=f"`{current_style}`", inline=True)
            embed.add_field(name="Status", value="🟢 Online", inline=True)
            
            await user.send(embed=embed)
            print(f"{Colors.GREEN}Commands sent to user {user.name}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Failed to send commands: {str(e)}{Colors.RESET}")

@bot.event
async def on_ready():
    print(ASCII_ART)
    print(f"{Colors.CYAN}Logged in as {bot.user}{Colors.RESET}")
    
    # Send commands to user
    await send_commands()
    
    # Server selection logic (same as before)
    servers = list(bot.guilds)
    if not servers:
        print(f"{Colors.RED}You're not in any servers!{Colors.RESET}")
        await bot.close()
        return

    print(f"\n{Colors.MAGENTA}=== SERVER SELECTION ==={Colors.RESET}")
    print(f"{Colors.YELLOW}Select a server by entering its number:{Colors.RESET}")
    for i, server in enumerate(servers):
        print(f"{Colors.CYAN}{i + 1}. 🏰 {server.name}{Colors.RESET}")
    print(f"{Colors.MAGENTA}========================={Colors.RESET}\n")

    while True:
        try:
            server_choice = int(input(f"{Colors.YELLOW}Enter server number: {Colors.RESET}")) - 1
            if server_choice < 0 or server_choice >= len(servers):
                raise ValueError("Invalid server number")
            break
        except ValueError:
            print(f"{Colors.RED}Invalid input. Try again.{Colors.RESET}")

    guild = servers[server_choice]
    print(f"\n{Colors.GREEN}Selected server: 🏰 {guild.name}{Colors.RESET}\n")

    voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
    if not voice_channels:
        print(f"{Colors.RED}No voice channels found in this server!{Colors.RESET}")
        await bot.close()
        return

    print(f"\n{Colors.MAGENTA}=== VOICE CHANNEL SELECTION ==={Colors.RESET}")
    print(f"{Colors.YELLOW}Select a voice channel by entering its number:{Colors.RESET}")
    for i, channel in enumerate(voice_channels):
        user_limit = channel.user_limit if channel.user_limit > 0 else "∞"
        status = f"{Colors.GREEN}✅ OPEN{Colors.RESET}" if len(channel.members) < channel.user_limit else f"{Colors.RED}❌ FULL{Colors.RESET}"
        print(f"{Colors.CYAN}{i + 1}. 🔊 {channel.name} (Users: {len(channel.members)}/{user_limit}, Status: {status}) {Colors.RESET}")
    print(f"{Colors.MAGENTA}==============================={Colors.RESET}\n")

    while True:
        try:
            channel_choice = int(input(f"{Colors.YELLOW}Enter voice channel number: {Colors.RESET}")) - 1
            if channel_choice < 0 or channel_choice >= len(voice_channels):
                raise ValueError("Invalid voice channel number")
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
            current_vc = await voice_channel.connect(reconnect=True, timeout=30)
            print(f"{Colors.GREEN}Successfully connected to 🔊 {voice_channel.name}{Colors.RESET}\n")
            break
        except asyncio.TimeoutError:
            print(f"{Colors.RED}Attempt {attempt + 1}/{retries}: Timeout while connecting. Retrying...{Colors.RESET}")
        except discord.Forbidden:
            print(f"{Colors.RED}ERROR: No permission to join or speak in this channel.{Colors.RESET}")
            await bot.close()
            return
        except Exception as e:
            print(f"{Colors.RED}CRITICAL FAILURE: Couldn't connect to 🔊 {voice_channel.name}. Error: {str(e)}{Colors.RESET}")
            if attempt == retries - 1:
                await bot.close()
                return
    else:
        print(f"{Colors.RED}Failed to connect to voice channel after {retries} attempts. Exiting...{Colors.RESET}")
        await bot.close()
        return

    # Play audio with current style
    try:
        style_config = AUDIO_STYLES[current_style]
        audio_source = discord.FFmpegPCMAudio("test.mp4", options=style_config['options'])
        current_vc.play(audio_source)
        print(f"{Colors.GREEN}Playing test.mp4 in 🔊 {voice_channel.name} with {current_style} style{Colors.RESET}\n")
        
        while True:
            await asyncio.sleep(5)
            if current_vc.channel != voice_channel:
                print(f"{Colors.YELLOW}Bot moved to a new voice channel: 🔊 {current_vc.channel.name}{Colors.RESET}")
                voice_channel = current_vc.channel
    except Exception as e:
        print(f"{Colors.RED}FATAL ERROR: {str(e)}{Colors.RESET}")
        await stop_audio()
    finally:
        await stop_audio()

@bot.event
async def on_message(message):
    # Only process DMs from authorized user
    if not isinstance(message.channel, discord.DMChannel) or str(message.author.id) != USER_ID:
        return

    print(f"{Colors.YELLOW}DM from {message.author}: {message.content}{Colors.RESET}")

    # Command handling
    if message.content.startswith('!'):
        cmd = message.content.lower().split()[0]
        
        try:
            if cmd == '!switch':
                parts = message.content.split()
                if len(parts) < 2:
                    await message.add_reaction('❌')
                    return

                channel_id = int(parts[1])
                target_channel = bot.get_channel(channel_id)
                
                if not target_channel or not isinstance(target_channel, discord.VoiceChannel):
                    await message.add_reaction('❌')
                    return

                await stop_audio()
                current_vc = await target_channel.connect(reconnect=True, timeout=30)
                current_vc.play(audio_source or discord.FFmpegPCMAudio("test.mp4", options=AUDIO_STYLES[current_style]['options']))
                await message.add_reaction('✅')

            elif cmd == '!stop':
                await stop_audio()
                await message.add_reaction('🛑')

            elif cmd == '!pause':
                if current_vc and current_vc.is_playing():
                    current_vc.pause()
                    await message.add_reaction('⏸️')

            elif cmd == '!resume':
                if current_vc and current_vc.is_paused():
                    current_vc.resume()
                    await message.add_reaction('▶️')

            elif cmd == '!style':
                parts = message.content.split()
                if len(parts) < 2:
                    await message.add_reaction('❌')
                    return

                style_name = parts[1].lower()
                success, msg = await change_style(style_name)
                if success:
                    await message.add_reaction('✅')
                else:
                    await message.add_reaction('❌')

            elif cmd == '!change':
                parts = message.content.split()
                if len(parts) < 2:
                    await message.add_reaction('❌')
                    return

                new_file = parts[1]
                success, msg = await change_audio(new_file)
                if success:
                    await message.add_reaction('✅')
                else:
                    await message.add_reaction('❌')

            elif cmd == '!list':
                files = [f for f in os.listdir('.') if f.endswith(('.mp3', '.mp4', '.wav'))]
                file_list = '\n'.join(files) if files else 'No audio files found'
                await message.channel.send(f"**Available audio files:**\n```{file_list}```")

            elif cmd == '!status':
                status = "🟢 Connected" if current_vc and current_vc.is_connected() else "🔴 Disconnected"
                playing = "▶️ Playing" if current_vc and current_vc.is_playing() else "⏸️ Paused"
                embed = discord.Embed(title="Bot Status", color=0x00ff00)
                embed.add_field(name="Connection", value=status, inline=True)
                embed.add_field(name="Audio", value=playing, inline=True)
                embed.add_field(name="Style", value=current_style, inline=True)
                embed.add_field(name="Channel", value=current_vc.channel.name if current_vc else "None", inline=True)
                await message.channel.send(embed=embed)

            elif cmd == '!help':
                await send_commands()

        except Exception as e:
            print(f"{Colors.RED}Command error: {str(e)}{Colors.RESET}")
            await message.add_reaction('💥')

if __name__ == "__main__":
    print(ASCII_ART)
    print(f"{Colors.CYAN}Setting up Audio Bot...{Colors.RESET}")
    
    # Setup dependencies
    check_ffmpeg()
    load_opus()
    
    # Setup audio file
    if not setup_audio_file():
        print(f"{Colors.RED}Failed to setup audio file. Exiting...{Colors.RESET}")
        sys.exit()
    
    # Validate token
    token = "MTIwMTkwNDY4NjE0ODM2MjM3MQ.G3IOYc.e6p5Ra0Tai5VCDvI55Q9Vd_h9QvUsFMGeoqKxo"
    validate_token(token)
    
    print(f"{Colors.GREEN}Setup complete! Starting bot...{Colors.RESET}")
    bot.run(token)
