import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")
    print(f"Loaded cogs: {list(bot.cogs.keys())}")

async def load_cogs():
    """Lade alle Cogs – MIT EXPLIZITER FEHLERausgabe"""
    
    # Liste aller Cogs die geladen werden sollen
    cog_files = ["moderation", "utility", "help"]
    
    for cog in cog_files:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ SUCCESS: Loaded {cog}")
        except Exception as e:
            print(f"❌ FAILED: {cog}")
            print(f"   Error: {type(e).__name__}: {e}")
    
    # Zusätzlich: Zeige alle Dateien im cogs Ordner
    import os
    print("\n📁 Files in cogs folder:")
    try:
        for file in os.listdir("./cogs"):
            print(f"   - {file}")
    except:
        print("   ❌ Could not read cogs folder!")

async def main():
    async with bot:
        await load_cogs()
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("❌ NO TOKEN FOUND!")
            return
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
