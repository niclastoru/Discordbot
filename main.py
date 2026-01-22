import discord
from discord.ext import commands
import random
import os
warn_data = {}
import json
import os

XP_FILE = "xp.json"

def load_xp():
    if not os.path.exists(XP_FILE):
        return {}
    with open(XP_FILE, "r") as f:
        return json.load(f)

def save_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=4)

xp_data = load_xp()

AUTORESPONDER_FILE = "autoresponder.json"

def load_autoresponder():
    if not os.path.exists(AUTORESPONDER_FILE):
        return {}
    with open(AUTORESPONDER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_autoresponder(data):
    with open(AUTORESPONDER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

autoresponder = load_autoresponder()

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

import json
import os

COIN_FILE = "coins.json"

def load_coins():
    if not os.path.exists(COIN_FILE):
        return {}
    with open(COIN_FILE, "r") as f:
        return json.load(f)

def save_coins(data):
    with open(COIN_FILE, "w") as f:
        json.dump(data, f, indent=4)

coins = load_coins()

@bot.command()
async def bal(ctx, member: discord.Member = None):
    member = member or ctx.author
    balance = coins.get(str(member.id), 0)

    await ctx.send(f"💰 **{member.display_name}** hat **{balance} Coins**.")

daily_claimed = set()

@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)

    if user_id in daily_claimed:
        await ctx.send("⏳ Du hast deine Daily Coins heute schon abgeholt.")
        return

    coins[user_id] = coins.get(user_id, 0) + 100
    save_coins(coins)
    daily_claimed.add(user_id)

    await ctx.send("🎁 Du hast **100 Coins** erhalten!")

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    sender = str(ctx.author.id)
    receiver = str(member.id)

    if amount <= 0:
        await ctx.send("❌ Ungültiger Betrag.")
        return

    if coins.get(sender, 0) < amount:
        await ctx.send("❌ Du hast nicht genug Coins.")
        return

    coins[sender] -= amount
    coins[receiver] = coins.get(receiver, 0) + amount
    save_coins(coins)

    await ctx.send(
        f"💸 {ctx.author.mention} hat {member.mention} **{amount} Coins** gesendet."
    )


@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)

    if user_id not in xp_data:
        await ctx.send("❌ Dieser User hat noch keine XP.")
        return

    level = xp_data[user_id]["level"]
    xp = xp_data[user_id]["xp"]

    await ctx.send(
        f"📊 **{member.display_name}**\n"
        f"⭐ Level: **{level}**\n"
        f"✨ XP: **{xp}**"
  @bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    xp_data.setdefault(user_id, {"xp": 0, "level": 1})

    xp_data[user_id]["xp"] += 5  # XP pro Nachricht

    current_xp = xp_data[user_id]["xp"]
    current_level = xp_data[user_id]["level"]

    # Level-Berechnung (einfach & stabil)
    needed_xp = current_level * 100

    if current_xp >= needed_xp:
        xp_data[user_id]["level"] += 1
        xp_data[user_id]["xp"] = 0
        await message.channel.send(
            f"🎉 {message.author.mention} ist jetzt **Level {xp_data[user_id]['level']}**!"
        )

    save_xp(xp_data)
    await bot.process_commands(message)
    )
@bot.command()
async def top(ctx):
    if not xp_data:
        await ctx.send("❌ Noch keine XP-Daten.")
        return

    sorted_users = sorted(
        xp_data.items(),
        key=lambda x: (x[1]["level"], x[1]["xp"]),
        reverse=True
    )

    text = ""
    for i, (user_id, data) in enumerate(sorted_users[:10], start=1):
        user = ctx.guild.get_member(int(user_id))
        if user:
            text += f"{i}. {user.display_name} — Level {data['level']}\n"

    await ctx.send(f"🏆 **Top 10 Levels**\n{text}")
    
# ===== RUN BOT (IMMER GANZ UNTEN!) =====
bot.run(os.environ["TOKEN"])
