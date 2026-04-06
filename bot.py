import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Lade Umgebungsvariablen
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Prüfe ob Token existiert
if not TOKEN:
    print("❌ DISCORD_TOKEN nicht gefunden! Setze den Token in Render Environment Variables.")
    exit(1)

# Intents setzen
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot initialisieren
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_cogs():
    """Lädt alle Cogs aus dem cogs Ordner"""
    cogs = ["cogs.moderation", "cogs.utility", "cogs.admin", "cogs.help"]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

@bot.event
async def on_ready():
    """Wird ausgeführt wenn der Bot bereit ist"""
    print(f"✅ Bot ist online als {bot.user.name}")
    print(f"📁 Bot ist auf {len(bot.guilds)} Servern")
    print(f"🔧 Geladene Cogs: {[cog.__class__.__name__ for cog in bot.cogs.values()]}")
    
    # Status setzen
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="!help"))

@bot.event
async def on_command_error(ctx, error):
    """Globaler Error Handler"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ {ctx.author.mention}, du hast keine Berechtigung für diesen Befehl!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Fehlendes Argument! Benutze `!help {ctx.command.name}` für Hilfe.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignoriere unbekannte Commands
    else:
        print(f"⚠️ Error: {error}")
        await ctx.send(f"❌ Ein Fehler ist aufgetreten: {error}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
