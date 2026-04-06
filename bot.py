import os
import discord
from discord.ext import commands
import asyncio

# Token direkt aus Environment Variable (Render setzt das automatisch)
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ DISCORD_TOKEN not found! Set it in Render Environment Variables.")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user.name}")
    print(f"📁 Servers: {len(bot.guilds)}")

async def load_cogs():
    cogs = ["cogs.moderation", "cogs.utility", "cogs.admin", "cogs.help"]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
