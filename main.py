import discord
from discord.ext import commands
import random
import json
import os

# ================== INTENTS ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=",", intents=intents)

# ================== FILES ==================
XP_FILE = "xp.json"
COIN_FILE = "coins.json"
AUTORESPONDER_FILE = "autoresponder.json"

# ================== LOAD / SAVE ==================
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

xp_data = load_json(XP_FILE)
coins = load_json(COIN_FILE)
autoresponder = load_json(AUTORESPONDER_FILE)
warn_data = {}

# ================== READY ==================
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

# ================== BASIC ==================
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

@bot.command()
async def ship(ctx, member: discord.Member):
    await ctx.send(f"💖 {ctx.author.display_name} × {member.display_name} = **{random.randint(0,100)}%**")

# ================== AVATAR ==================
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Avatar von {member}", color=discord.Color.blue())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

# ================== USERINFO ==================
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Userinfo – {member}", color=discord.Color.blurple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Account erstellt", value=member.created_at.strftime("%d.%m.%Y"))
    embed.add_field(name="Server beigetreten", value=member.joined_at.strftime("%d.%m.%Y"))
    roles = ", ".join(r.name for r in member.roles[1:]) or "Keine"
    embed.add_field(name="Rollen", value=roles, inline=False)
    await ctx.send(embed=embed)

# ================== JAIL ==================
@bot.command()
@commands.has_permissions(moderate_members=True)
async def jail(ctx, member: discord.Member, *, reason="Kein Grund"):
    role = discord.utils.get(ctx.guild.roles, name="jailed")
    if not role:
        await ctx.send("❌ Rolle **jailed** existiert nicht.")
        return
    await member.add_roles(role)
    await ctx.send(f"🔒 {member.mention} wurde gejailt | **{reason}**")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unjail(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="jailed")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"🔓 {member.mention} wurde entjailt")

# ================== WARN ==================
@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason="Kein Grund"):
    warn_data.setdefault(str(member.id), []).append(reason)
    await ctx.send(f"⚠️ {member.mention} verwarnt | **{reason}**")
    try:
        await member.send(f"⚠️ Du wurdest auf **{ctx.guild.name}** verwarnt\nGrund: {reason}")
    except:
        pass

@bot.command()
async def warnings(ctx, member: discord.Member):
    warns = warn_data.get(str(member.id), [])
    if not warns:
        await ctx.send("✅ Keine Verwarnungen")
        return
    text = "\n".join(f"{i+1}. {w}" for i, w in enumerate(warns))
    await ctx.send(f"⚠️ Verwarnungen:\n{text}")

# ================== ECONOMY ==================
@bot.command()
async def bal(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"💰 {member.display_name}: **{coins.get(str(member.id),0)} Coins**")

@bot.command()
async def daily(ctx):
    coins[str(ctx.author.id)] = coins.get(str(ctx.author.id),0) + 100
    save_json(COIN_FILE, coins)
    await ctx.send("🎁 Du hast **100 Coins** bekommen!")

# ================== XP / LEVEL ==================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    xp_data.setdefault(uid, {"xp":0,"level":1})
    xp_data[uid]["xp"] += 5

    need = xp_data[uid]["level"] * 100
    if xp_data[uid]["xp"] >= need:
        xp_data[uid]["xp"] = 0
        xp_data[uid]["level"] += 1
        await message.channel.send(f"🎉 {message.author.mention} ist jetzt Level **{xp_data[uid]['level']}**")

    save_json(XP_FILE, xp_data)

    # autoresponder
    msg = message.content.lower()
    if msg in autoresponder:
        await message.channel.send(autoresponder[msg])

    await bot.process_commands(message)

@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = xp_data.get(str(member.id))
    if not data:
        await ctx.send("❌ Keine XP")
        return
    await ctx.send(f"⭐ {member.display_name} | Level {data['level']} | XP {data['xp']}")

@bot.command()
async def top(ctx):
    sorted_users = sorted(xp_data.items(), key=lambda x:(x[1]["level"],x[1]["xp"]), reverse=True)
    text = ""
    for i,(uid,data) in enumerate(sorted_users[:10],1):
        user = ctx.guild.get_member(int(uid))
        if user:
            text += f"{i}. {user.display_name} – Level {data['level']}\n"
    await ctx.send(f"🏆 **Top 10**\n{text}")

# ================== AUTORESPONDER ==================
@bot.command()
@commands.has_permissions(administrator=True)
async def ar_add(ctx, *, text):
    trigger, response = map(str.strip, text.split("|",1))
    autoresponder[trigger.lower()] = response
    save_json(AUTORESPONDER_FILE, autoresponder)
    await ctx.send("✅ AutoResponder hinzugefügt")

@bot.command()
async def ar_list(ctx):
    if not autoresponder:
        await ctx.send("❌ Keine AutoResponder")
        return
    await ctx.send("\n".join(f"- {k}" for k in autoresponder))

# ================== RUN ==================
bot.run(os.environ["TOKEN"])
