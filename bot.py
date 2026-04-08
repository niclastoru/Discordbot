import os
import discord
from discord.ext import commands
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Standard Help Command entfernen (wichtig!)
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user.name}")
    print(f"📁 Servers: {len(bot.guilds)}")
    print(f"📁 Loaded cogs: {list(bot.cogs.keys())}")
    print(f"🔧 Total commands: {len(bot.commands)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ Missing permission: {error.missing_permissions[0]}")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument. Use `!help {ctx.command.name}`")
    else:
        print(f"Error: {error}")

async def load_cogs():
    cogs = ["cogs.help", "cogs.moderation", "cogs.utility", "cogs.admin"]
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
