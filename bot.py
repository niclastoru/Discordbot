import os
import discord
from discord.ext import commands
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ Kein Token gefunden!")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ENTFERNT DEN STANDARD HELP COMMAND
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user.name}")
    print(f"📁 Geladene Cogs: {list(bot.cogs.keys())}")
    print(f"🔧 Commands: {len(bot.commands)}")

async def load_cogs():
    cogs = ["cogs.moderation", "cogs.utility", "cogs.admin", "cogs.help"]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Geladen: {cog}")
        except Exception as e:
            print(f"❌ Fehler bei {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

