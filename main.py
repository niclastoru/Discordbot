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
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if reason is None:
        reason = "Kein Grund angegeben"

    try:
        await member.ban(reason=reason)
        await ctx.send(
            f"🔨 **{member}** wurde gebannt.\n📄 **Grund:** {reason}"
        )
    except discord.Forbidden:
        await ctx.send("❌ Ich habe keine Rechte, diesen User zu bannen.")
    except discord.HTTPException:
        await ctx.send("❌ Fehler beim Bannen.")
@bot.command()
@commands.has_permissions(moderate_members=True)
async def jail(ctx, member: discord.Member, *, reason="Kein Grund angegeben"):
    jail_role = discord.utils.get(ctx.guild.roles, name="Jail")

    if not jail_role:
        await ctx.send("❌ Jail-Rolle existiert nicht.")
        return

    if jail_role in member.roles:
        await ctx.send("⚠️ User ist bereits im Jail.")
        return

    await member.add_roles(jail_role, reason=reason)
    await ctx.send(f"🔒 {member.mention} wurde gejailt.\n📝 Grund: **{reason}**")
