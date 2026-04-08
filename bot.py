import os
import discord
from discord.ext import commands
import asyncio
import nest_asyncio
nest_asyncio.apply()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Auto-load alle .py files im cogs Ordner
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "help.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")
    await load_cogs()
    
    # Help Cog separat laden (nach den anderen)
    try:
        await bot.load_extension("cogs.help")
        print("✅ Loaded help.py")
    except:
        print("⚠️ No help.py found")

bot.run("DISCORD_TOKEN")
