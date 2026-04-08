import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# WICHTIG: Standard help command deaktivieren
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")
    print(f"Loaded cogs: {list(bot.cogs.keys())}")

async def main():
    async with bot:
        await load_cogs()
        token = os.getenv("DISCORD_TOKEN")
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
