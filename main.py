import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="?",
    intents=intents,
    case_insensitive=True,
    help_command=None
)

# ================= READY =================

@bot.event
async def on_ready():
    print(f"🔥 {bot.user} is online")

# ================= LOAD COGS =================

@bot.event
async def setup_hook():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")

# ================= ERROR SYSTEM =================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):
        return await ctx.send(embed=discord.Embed(
            title="❌ No Permission",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        ))

    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(embed=discord.Embed(
            title="⚠️ Wrong Usage",
            description=f"Usage: `?{ctx.command.name} {ctx.command.signature}`",
            color=discord.Color.orange()
        ))

    elif isinstance(error, commands.BadArgument):
        return await ctx.send(embed=discord.Embed(
            title="❌ Invalid Input",
            description=f"Usage: `?{ctx.command.name} {ctx.command.signature}`",
            color=discord.Color.red()
        ))

    elif isinstance(error, commands.CommandNotFound):
        return

    else:
        print(error)

# ================= PING =================

@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {round(bot.latency * 1000)}ms",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

bot.run(TOKEN)
