import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")  # oder direkt "DEIN_TOKEN"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="_", intents=intents)

# ================= READY =================
@bot.event
async def on_ready():
    print(f"🛡️ Jerry online als {bot.user}")

# ================= ROLE (ADD + REMOVE) =================
@bot.command(aliases=["r"])
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role_name: str):

    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if not role:
        embed = discord.Embed(
            title="❌ Fehler",
            description=f"Rolle **{role_name}** nicht gefunden.",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    if role in member.roles:
        await member.remove_roles(role)

        embed = discord.Embed(
            title="🗑️ Rolle entfernt",
            description=f"{role.mention} wurde von {member.mention} entfernt",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    else:
        await member.add_roles(role)

        embed = discord.Embed(
            title="✅ Rolle hinzugefügt",
            description=f"{member.mention} hat jetzt {role.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

# ================= JAIL =================
@bot.command()
@commands.has_permissions(moderate_members=True)
async def jail(ctx, member: discord.Member, *, reason="Kein Grund angegeben"):

    role = discord.utils.get(ctx.guild.roles, name="jailed")

    if not role:
        embed = discord.Embed(
            title="❌ Fehler",
            description="Rolle **jailed** existiert nicht.",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    await member.add_roles(role)

    embed = discord.Embed(
        title="🔒 User gejailt",
        description=f"{member.mention} wurde gejailt\n📝 Grund: **{reason}**",
        color=discord.Color.dark_red()
    )
    await ctx.send(embed=embed)

# ================= UNJAIL =================
@bot.command()
@commands.has_permissions(moderate_members=True)
async def unjail(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="jailed")

    if role in member.roles:
        await member.remove_roles(role)

        embed = discord.Embed(
            title="🔓 User entlassen",
            description=f"{member.mention} wurde entjailt",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

# ================= BAN =================
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Kein Grund angegeben"):

    try:
        await member.send(f"🚫 Du wurdest gebannt von {ctx.guild.name}\nGrund: {reason}")
    except:
        pass

    await ctx.guild.ban(member, reason=reason)

    embed = discord.Embed(
        title="🔨 User gebannt",
        description=f"{member} wurde gebannt\n📝 Grund: **{reason}**",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# ================= UNBAN =================
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):

    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

    embed = discord.Embed(
        title="✅ User entbannt",
        description=f"{user} wurde entbannt",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# ================= RUN =================
bot.run(TOKEN)
