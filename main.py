import discord
from discord.ext import commands
import random
import os
warn_data = {}

# ===== INTENTS =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=",", intents=intents)

# ===== READY =====
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

# ===== BASIC COMMANDS =====
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

@bot.command()
async def ship(ctx, member: discord.Member):
    love = random.randint(0, 100)
    await ctx.send(
        f"💖 {ctx.author.display_name} × {member.display_name} = **{love}% Liebe**"
    )

# ===== ROLE COMMAND =====
@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send("❌ Rolle nicht gefunden.")
        return

    await member.add_roles(role)
    await ctx.send(f"✅ Rolle **{role.name}** wurde {member.display_name} gegeben.")

# ===== BAN COMMAND =====
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Kein Grund angegeben"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 **{member}** wurde gebannt.\n📄 **Grund:** {reason}")
    except discord.Forbidden:
        await ctx.send("❌ Ich habe keine Rechte.")
    except discord.HTTPException:
        await ctx.send("❌ Fehler beim Bannen.")

# ===== JAIL SYSTEM =====
@bot.command()
@commands.has_permissions(moderate_members=True)
async def jail(ctx, member: discord.Member, *, reason="Kein Grund angegeben"):
    jail_role = discord.utils.get(ctx.guild.roles, name="jailed")

    if not jail_role:
        await ctx.send("❌ Jail-Rolle existiert nicht.")
        return

    if jail_role in member.roles:
        await ctx.send("⚠️ User ist bereits im Jail.")
        return

    await member.add_roles(jail_role, reason=reason)
    await ctx.send(f"🔒 {member.mention} wurde gejailt.\n📝 Grund: **{reason}**")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unjail(ctx, member: discord.Member):
    jail_role = discord.utils.get(ctx.guild.roles, name="jailed")

    if not jail_role:
        await ctx.send("❌ Jail-Rolle existiert nicht.")
        return

    if jail_role not in member.roles:
        await ctx.send("⚠️ User ist nicht im Jail.")
        return

    await member.remove_roles(jail_role)
    await ctx.send(f"🔓 {member.mention} wurde entjailt.")

# ===== MARRY SYSTEM =====
marriages = {}  # user_id : partner_id

@bot.command()
async def marry(ctx, member: discord.Member):
    if member.bot:
        await ctx.send("🤖 Bots kann man nicht heiraten.")
        return

    if member == ctx.author:
        await ctx.send("💀 Du kannst dich nicht selbst heiraten.")
        return

    if ctx.author.id in marriages:
        await ctx.send("❌ Du bist bereits verheiratet.")
        return

    if member.id in marriages:
        await ctx.send("❌ Diese Person ist bereits verheiratet.")
        return

    marriages[ctx.author.id] = member.id
    marriages[member.id] = ctx.author.id

    await ctx.send(
        f"💍 **{ctx.author.mention} und {member.mention} sind jetzt verheiratet!** 🎉"
    )

@bot.command()
async def divorce(ctx):
    if ctx.author.id not in marriages:
        await ctx.send("❌ Du bist nicht verheiratet.")
        return

    partner_id = marriages[ctx.author.id]
    partner = ctx.guild.get_member(partner_id)

    del marriages[partner_id]
    del marriages[ctx.author.id]

    if partner:
        await ctx.send(
            f"💔 **{ctx.author.mention} und {partner.mention} sind jetzt geschieden.**"
        )
    else:
        await ctx.send("💔 Ehe beendet.")

@bot.command()
async def marrystatus(ctx):
    if ctx.author.id not in marriages:
        await ctx.send("💔 Du bist aktuell nicht verheiratet.")
        return

    partner_id = marriages[ctx.author.id]
    partner = ctx.guild.get_member(partner_id)

    if partner:
        await ctx.send(f"💍 Du bist mit **{partner.mention}** verheiratet.")
    else:
        await ctx.send("💍 Du bist verheiratet, aber dein Partner ist nicht auf dem Server.")
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    embed = discord.Embed(
        title=f"🖼️ Avatar von {member}",
        color=discord.Color.blue()
    )
    embed.set_image(url=member.avatar.url)
    embed.set_footer(text=f"Angefordert von {ctx.author}")

    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    embed = discord.Embed(
        title=f"👤 Userinfo von {member}",
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    embed.add_field(name="🆔 ID", value=member.id, inline=False)
    embed.add_field(name="📅 Account erstellt", value=member.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="📥 Server beigetreten", value=member.joined_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(
        name="🎭 Rollen",
        value=", ".join([role.mention for role in member.roles[1:]]) or "Keine",
        inline=False
    )

    embed.set_footer(text=f"Angefordert von {ctx.author}", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)

# ===== WARN SYSTEM =====

warnings = {}  # user_id : list of reasons

@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason="Kein Grund angegeben"):
    user_warnings = warn_data.get(member.id, [])
    user_warnings.append(reason)
    warn_data[member.id] = user_warnings

    try:
        await member.send(
            f"⚠️ **Du wurdest auf {ctx.guild.name} verwarnt!**\n"
            f"📄 **Grund:** {reason}\n"
            f"📌 **Verwarnungen:** {len(user_warnings)}"
        )
    except discord.Forbidden:
        await ctx.send("⚠️ Konnte keine DM senden (DMs geschlossen).")

    await ctx.send(
        f"⚠️ {member.mention} wurde verwarnt.\n"
        f"📄 Grund: **{reason}**\n"
        f"📌 Verwarnungen: **{len(user_warnings)}**"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: discord.Member):
    user_warnings = warn_data.get(member.id)

    if not user_warnings:
        await ctx.send(f"✅ {member.mention} hat keine Verwarnungen.")
        return

    text = "\n".join([f"{i+1}. {w}" for i, w in enumerate(user_warnings)])
    await ctx.send(
        f"⚠️ **Verwarnungen von {member.display_name}:**\n{text}"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def clearwarnings(ctx, member: discord.Member):
    if member.id not in warn_data:
        await ctx.send("ℹ️ User hat keine Verwarnungen.")
        return

    del warn_data[member.id]
    await ctx.send(f"🧹 Verwarnungen von {member.mention} wurden gelöscht.")

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Du hast keine Rechte für diesen Command.")
        
# ===== RUN BOT (IMMER GANZ UNTEN!) =====
bot.run(os.environ["TOKEN"])
