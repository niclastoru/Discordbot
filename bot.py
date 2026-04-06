import os
import discord
from discord.ext import commands
import asyncio
import traceback

print("🔵 Bot wird gestartet...")

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ KEIN TOKEN GEFUNDEN!")
    exit(1)

print("✅ Token gefunden")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

print("🔵 Bot-Objekt erstellt")

@bot.event
async def on_ready():
    print(f"✅✅✅ BOT IST ONLINE: {bot.user.name} ✅✅✅")
    print(f"📁 Geladene Cogs: {list(bot.cogs.keys())}")
    print(f"🔧 Befehle: {len(bot.commands)}")
    
    # Test-Command direkt hinzufügen
    @bot.command()
    async def ping(ctx):
        await ctx.send("Pong! Bot läuft!")

async def load_cogs():
    print("🔵 Lade Cogs...")
    
    # Liste alle Dateien im cogs Ordner
    try:
        files = os.listdir("cogs")
        print(f"📁 Dateien in cogs/: {files}")
    except Exception as e:
        print(f"❌ Kann cogs Ordner nicht lesen: {e}")
    
    cogs_list = ["cogs.moderation", "cogs.utility", "cogs.admin", "cogs.help"]
    
    for cog in cogs_list:
        print(f"🔵 Versuche zu laden: {cog}")
        try:
            await bot.load_extension(cog)
            print(f"✅ GELADEN: {cog}")
        except Exception as e:
            print(f"❌ FEHLER bei {cog}:")
            print(f"   Fehler: {type(e).__name__}: {e}")
            traceback.print_exc()

@bot.event
async def on_command_error(ctx, error):
    print(f"⚠️ Command Error: {error}")
    await ctx.send(f"Fehler: {error}")

print("🔵 Starte main...")

async def main():
    print("🔵 In main()")
    async with bot:
        print("🔵 Lade Cogs...")
        await load_cogs()
        print(f"🔵 Cogs nach dem Laden: {list(bot.cogs.keys())}")
        print("🔵 Starte Bot...")
        await bot.start(TOKEN)

if __name__ == "__main__":
    print("🔵 Führe asyncio.run(main()) aus...")
    asyncio.run(main())
