import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    print(f"✅ Bot ist auf {len(bot.guilds)} Servern")
    print(f"📁 Geladene Cogs: {list(bot.cogs.keys())}")

async def load_cogs():
    """Lädt alle Cogs aus dem Hauptverzeichnis"""
    cogs = [
        "moderation",
        "admin",
        "settings",
        "servers",
        "giveaway",
        "logs",
        "fun",
        "leveling",
        "utility",
        "help"
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ {cog} geladen")
        except Exception as e:
            print(f"❌ {cog} Fehler: {e}")

async def main():
    async with bot:
        await load_cogs()
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("❌ Kein Discord Token gefunden!")
            return
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
