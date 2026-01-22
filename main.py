import discord
from discord.ext import commands
import random
import os
import json
from openai import OpenAI

# ================= OPENAI =================
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def ask_ai(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Du bist ein cooler, respektvoller Discord-Bot."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.8
    )
    return response.choices[0].message.content

# ================= FILES =================
XP_FILE = "xp.json"
COIN_FILE = "coins.json"
AUTORESPONDER_FILE = "autoresponder.json"

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

xp_data = load_json(XP_FILE, {})
coins = load_json(COIN_FILE, {})
autoresponder = load_json(AUTORESPONDER_FILE, {})
warn_data = {}
marriages = {}

# ================= BOT =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=",", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

# ================= BASIC =================
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

@bot.command()
async def ship(ctx, member: discord.Member):
    await ctx.send(f"💖 {ctx.author.display_name} × {member.display_name} = **{random.randint(0,100)}%**")

@bot.command()
async def ai(ctx, *, frage: str):
    await ctx.send(await ask_ai(frage))

# ================= ROLE =================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        return await ctx.send("❌ Rolle nicht gefunden")
    await member.add_roles(role)
    await ctx.send(f"✅ {role.name} gegeben")

# ================= AVATAR / USERINFO =================
@bot.command()
async def avatar(ctx, member: discord.Member=None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Avatar von {member}")
    embed.set_image(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member=None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Userinfo: {member}")
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Beigetreten", value=member.joined_at.strftime("%d.%m.%Y"))
    await ctx.send(embed=embed)

# ================= MODERATION =================
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Kein Grund"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member} gebannt")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def jail(ctx, member: discord.Member, *, reason="Kein Grund"):
    role = discord.utils.get(ctx.guild.roles, name="jailed")
    if not role:
        return await ctx.send("❌ Rolle `jailed` fehlt")
    await member.add_roles(role)
    await ctx.send(f"🔒 {member.mention} gejailt")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unjail(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="jailed")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"🔓 {member.mention} entjailt")

@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason="Kein Grund"):
    warn_data.setdefault(str(member.id), []).append(reason)
    await ctx.send(f"⚠️ {member.mention} verwarnt")

@bot.command()
async def warnings(ctx, member: discord.Member):
    warns = warn_data.get(str(member.id), [])
    if not warns:
        return await ctx.send("✅ Keine Verwarnungen")
    await ctx.send("\n".join(warns))

@bot.command()
@commands.has_permissions(administrator=True)
async def clearwarnings(ctx, member: discord.Member):
    warn_data.pop(str(member.id), None)
    await ctx.send("🧹 Verwarnungen gelöscht")

# ================= MARRY =================
@bot.command()
async def marry(ctx, member: discord.Member):
    if ctx.author.id in marriages:
        return await ctx.send("❌ Du bist verheiratet")
    marriages[ctx.author.id] = member.id
    marriages[member.id] = ctx.author.id
    await ctx.send(f"💍 {ctx.author.mention} ❤️ {member.mention}")

@bot.command()
async def divorce(ctx):
    partner = marriages.pop(ctx.author.id, None)
    if partner:
        marriages.pop(partner, None)
        await ctx.send("💔 Geschieden")

@bot.command()
async def marrystatus(ctx):
    partner = marriages.get(ctx.author.id)
    if not partner:
        return await ctx.send("❌ Nicht verheiratet")
    await ctx.send(f"💍 Verheiratet mit <@{partner}>")

# ================= ECONOMY =================
@bot.command()
async def bal(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(f"💰 {coins.get(str(member.id),0)} Coins")

@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    coins[uid] = coins.get(uid,0) + 100
    save_json(COIN_FILE, coins)
    await ctx.send("🎁 +100 Coins")

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    sender = str(ctx.author.id)
    if coins.get(sender,0) < amount:
        return await ctx.send("❌ Nicht genug Coins")
    coins[sender] -= amount
    coins[str(member.id)] = coins.get(str(member.id),0) + amount
    save_json(COIN_FILE, coins)
    await ctx.send("💸 Gesendet")

# ================= XP =================
@bot.command()
async def rank(ctx, member: discord.Member=None):
    member = member or ctx.author
    data = xp_data.get(str(member.id))
    if not data:
        return await ctx.send("❌ Keine XP")
    await ctx.send(f"⭐ Level {data['level']} | XP {data['xp']}")

@bot.command()
async def top(ctx):
    sorted_users = sorted(xp_data.items(), key=lambda x: x[1]["level"], reverse=True)
    text = ""
    for i,(uid,data) in enumerate(sorted_users[:10],1):
        user = ctx.guild.get_member(int(uid))
        if user:
            text += f"{i}. {user.display_name} – Lvl {data['level']}\n"
    await ctx.send(text)

# ================= AUTORESPONDER =================
@bot.command()
@commands.has_permissions(administrator=True)
async def ar_add(ctx, *, text):
    trigger, response = map(str.strip, text.split("|",1))
    autoresponder[trigger.lower()] = response
    save_json(AUTORESPONDER_FILE, autoresponder)
    await ctx.send("✅ AutoResponder hinzugefügt")

@bot.command()
async def ar_list(ctx):
    await ctx.send("\n".join(autoresponder.keys()) or "❌ Keine")

@bot.command()
@commands.has_permissions(administrator=True)
async def ar_remove(ctx, *, trigger):
    autoresponder.pop(trigger.lower(),None)
    save_json(AUTORESPONDER_FILE, autoresponder)
    await ctx.send("🗑️ Entfernt")

# ================= MESSAGE EVENT =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    xp_data.setdefault(uid, {"xp":0,"level":1})
    xp_data[uid]["xp"] += 5

    if xp_data[uid]["xp"] >= xp_data[uid]["level"]*100:
        xp_data[uid]["xp"] = 0
        xp_data[uid]["level"] += 1
        await message.channel.send(f"🎉 {message.author.mention} Level Up!")

    save_json(XP_FILE, xp_data)

    if message.content.lower() in autoresponder:
        await message.channel.send(autoresponder[message.content.lower()])

    await bot.process_commands(message)

# ================= RUN =================
bot.run(os.environ["TOKEN"])
