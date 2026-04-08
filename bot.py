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

@bot.command(name="cogs")
@commands.is_owner()
async def show_cogs(ctx):
    """Zeigt alle geladenen Cogs (Owner only)"""
    cogs_list = "\n".join([f"✅ {cog}" for cog in bot.cogs.keys()])
    embed = discord.Embed(title="📁 Geladene Cogs", description=cogs_list or "Keine!", color=0x57F287)
    await ctx.send(embed=embed)

@bot.command(name="load")
@commands.is_owner()
async def load_cog(ctx, cog_name: str):
    """Lade einen Cog manuell (Owner only)"""
    try:
        await bot.load_extension(cog_name)
        await ctx.send(f"✅ {cog_name} geladen")
    except Exception as e:
        await ctx.send(f"❌ Fehler: {e}")

@bot.command(name="reload")
@commands.is_owner()
async def reload_cog(ctx, cog_name: str):
    """Relade einen Cog (Owner only)"""
    try:
        await bot.reload_extension(cog_name)
        await ctx.send(f"✅ {cog_name} neugeladen")
    except Exception as e:
        await ctx.send(f"❌ Fehler: {e}")

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
