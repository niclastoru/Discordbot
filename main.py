import discord
from discord.ext import commands
import random
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=",", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

@bot.command()
async def ship(ctx, member: discord.Member):
    love = random.randint(0, 100)
    await ctx.send(
        f"💖 {ctx.author.display_name} × {member.display_name} = **{love}% Liebe**"
    )

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send("❌ Rolle nicht gefunden.")
        return

    await member.add_roles(role)
    await ctx.send(f"✅ Rolle **{role.name}** wurde {member.display_name} gegeben.")

bot.run(os.environ["TOKEN"])
