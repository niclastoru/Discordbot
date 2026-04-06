import os
import discord
from discord.ext import commands
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ No token found!")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Remove default help command
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user.name}")
    print(f"📁 Servers: {len(bot.guilds)}")
    print(f"📁 Loaded cogs: {list(bot.cogs.keys())}")
    print(f"🔧 Total commands: {len(bot.commands)}")

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
