import os
import discord
from discord.ext import commands
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ========== HELP (automatisch, ohne extra Cog) ==========
@bot.command()
async def help(ctx, command_name: str = None):
    if command_name:
        cmd = bot.get_command(command_name.lower())
        if cmd:
            embed = discord.Embed(title=f"📖 {cmd.name}", description=cmd.help or "No description", color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Command not found")
        return
    
    # Sammle alle Commands aus allen Cogs
    cogs_dict = {}
    for cmd in bot.commands:
        if cmd.name == "help":
            continue
        cog_name = cmd.cog.__class__.__name__ if cmd.cog else "Other"
        if cog_name not in cogs_dict:
            cogs_dict[cog_name] = []
        cogs_dict[cog_name].append(f"`!{cmd.name}`")
    
    embed = discord.Embed(title="📖 Bot Commands", color=discord.Color.blue())
    for cog_name, cmds in cogs_dict.items():
        embed.add_field(name=f"{cog_name} ({len(cmds)})", value="\n".join(cmds[:20]), inline=True)
    
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user.name}")
    print(f"📁 Cogs: {list(bot.cogs.keys())}")

async def load_cogs():
    cogs = ["cogs.moderation", "cogs.utility", "cogs.admin", "cogs.settings"]
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
