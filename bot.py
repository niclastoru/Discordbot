import discord
from discord.ext import commands
import os
import asyncio

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")
    print(f"Loaded cogs: {list(bot.cogs.keys())}")

async def load_cogs():
    """Lade alle Cogs aus dem cogs Ordner"""
    try:
        # Versuche verschiedene Pfade
        cog_paths = ["./cogs", "cogs"]
        
        for path in cog_paths:
            if os.path.exists(path):
                for filename in os.listdir(path):
                    if filename.endswith(".py"):
                        try:
                            await bot.load_extension(f"cogs.{filename[:-3]}")
                            print(f"✅ Loaded {filename}")
                        except Exception as e:
                            print(f"❌ Failed {filename}: {e}")
                break
    except Exception as e:
        print(f"Error loading cogs: {e}")

async def main():
    async with bot:
        await load_cogs()
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("❌ No DISCORD_TOKEN found in environment variables!")
            return
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
