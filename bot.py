import os
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Standard Help Command entfernen
bot.remove_command("help")

# ========== HELP COMMAND (DIREKT IN BOT.PY) ==========
@bot.command()
async def help(ctx, command_name: str = None):
    """Shows all commands or info about a specific command"""
    
    if command_name:
        cmd = bot.get_command(command_name.lower())
        if cmd:
            embed = discord.Embed(
                title=f"📖 Command: {cmd.name}",
                description=cmd.help or "No description",
                color=discord.Color.blue()
            )
            usage = f"`!{cmd.name}"
            if cmd.signature:
                usage += f" {cmd.signature}"
            usage += "`"
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Command `{command_name}` not found.")
        return
    
    # Alle Commands aus allen Cogs sammeln
    categories = {}
    for cmd in bot.commands:
        if cmd.name == "help":
            continue
        cog_name = cmd.cog.__class__.__name__ if cmd.cog else "Other"
        if cog_name not in categories:
            categories[cog_name] = []
        categories[cog_name].append(f"`!{cmd.name}`")
    
    embed = discord.Embed(
        title="📖 Bot Commands",
        description="Use `!help <command>` for more details.",
        color=discord.Color.blue()
    )
    
    for cog_name, cmds in categories.items():
        embed.add_field(
            name=f"{cog_name} ({len(cmds)})",
            value="\n".join(cmds[:20]),
            inline=True
        )
    
    total = sum(len(cmds) for cmds in categories.values())
    embed.set_footer(text=f"Total: {total} commands")
    await ctx.send(embed=embed)

# ========== ON READY ==========
@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user.name}")
    print(f"📁 Servers: {len(bot.guilds)}")
    print(f"📁 Loaded cogs: {list(bot.cogs.keys())}")
    print(f"🔧 Total commands: {len(bot.commands)}")

# ========== ERROR HANDLER ==========
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

# ========== COGS LADEN ==========
async def load_cogs():
    cogs = ["cogs.moderation", "cogs.utility", "cogs.admin"]
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
