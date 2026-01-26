# ================== IMPORTS ==================
import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import ButtonStyle
import random, json, os, re

# ================== INTENTS ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=",", intents=intents)

# ================== FILE UTILS ==================
def load(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

xp = load("xp.json", {})
coins = load("coins.json", {})
warnings = load("warnings.json", {})
akten = load("akten.json", {})
marriages = load("marriages.json", {})
autoresponder = load("autoresponder.json", {})

# ================== READY ==================
@bot.event
async def on_ready():
    print(f"✅ Online als {bot.user}")

# ================== LINK BLOCK ==================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if re.search(r"(discord\.gg/|discord\.com/invite)", message.content.lower()):
        if not message.author.guild_permissions.administrator:
            await message.delete()
            await message.channel.send(
                f"❌ {message.author.mention} Discord-Server-Links sind verboten!",
                delete_after=5
            )
            return

    uid = str(message.author.id)
    xp.setdefault(uid, {"xp": 0, "level": 1})
    xp[uid]["xp"] += 5

    if xp[uid]["xp"] >= xp[uid]["level"] * 100:
        xp[uid]["xp"] = 0
        xp[uid]["level"] += 1
        await message.channel.send(
            f"🎉 {message.author.mention} ist jetzt Level **{xp[uid]['level']}**"
        )

    save("xp.json", xp)

    if message.content.lower() in autoresponder:
        await message.channel.send(autoresponder[message.content.lower()])

    await bot.process_commands(message)

# ================== BASIC ==================
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

@bot.command()
async def ship(ctx, member: discord.Member):
    await ctx.send(f"💖 {ctx.author.display_name} × {member.display_name} = **{random.randint(0,100)}%**")

# ================== USER ==================
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    e = discord.Embed(title=f"Avatar von {member}")
    e.set_image(url=member.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def banner(ctx, member: discord.Member = None):
    member = member or ctx.author
    user = await bot.fetch_user(member.id)
    if not user.banner:
        await ctx.send("❌ Kein Banner vorhanden.")
        return
    e = discord.Embed(title=f"Banner von {member}")
    e.set_image(url=user.banner.url)
    await ctx.send(embed=e)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    e = discord.Embed(title=f"Userinfo – {member}")
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="ID", value=member.id)
    e.add_field(name="Account", value=member.created_at.strftime("%d.%m.%Y"))
    e.add_field(name="Server Join", value=member.joined_at.strftime("%d.%m.%Y"))
    roles = ", ".join(r.mention for r in member.roles[1:]) or "Keine"
    e.add_field(name="Rollen", value=roles, inline=False)
    await ctx.send(embed=e)

# ================== SERVER ==================
@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    e = discord.Embed(title=g.name)
    e.set_thumbnail(url=g.icon.url if g.icon else None)
    e.add_field(name="Owner", value=g.owner)
    e.add_field(name="Mitglieder", value=g.member_count)
    e.add_field(name="Boosts", value=g.premium_subscription_count)
    await ctx.send(embed=e)

# ================== ECONOMY ==================
@bot.command()
async def bal(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"💰 {member.display_name}: {coins.get(str(member.id),0)} Coins")

@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    coins[uid] = coins.get(uid, 0) + 100
    save("coins.json", coins)
    await ctx.send("🎁 +100 Coins")

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    uid = str(ctx.author.id)
    tid = str(member.id)
    if coins.get(uid,0) < amount:
        await ctx.send("❌ Zu wenig Coins")
        return
    coins[uid] -= amount
    coins[tid] = coins.get(tid,0) + amount
    save("coins.json", coins)
    await ctx.send("💸 Gesendet!")

# ================== RANK ==================
@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = xp.get(str(member.id))
    await ctx.send(f"⭐ Level {data['level']} | XP {data['xp']}")

@bot.command()
async def top(ctx):
    s = sorted(xp.items(), key=lambda x:(x[1]["level"],x[1]["xp"]), reverse=True)
    msg = ""
    for i,(uid,d) in enumerate(s[:10],1):
        u = ctx.guild.get_member(int(uid))
        if u:
            msg += f"{i}. {u.display_name} – L{d['level']}\n"
    await ctx.send(msg)

# ================== WARN / JAIL / AKTE ==================
@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="Kein Grund"):
    warnings.setdefault(str(member.id), []).append(reason)
    save("warnings.json", warnings)
    await ctx.send("⚠️ Verwarnt")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def jail(ctx, member: discord.Member, *, reason="Kein Grund"):
    role = discord.utils.get(ctx.guild.roles, name="jailed")
    if not role:
        await ctx.send("❌ Rolle jailed fehlt")
        return
    await member.add_roles(role)
    akten.setdefault(str(member.id), {"jails":0})
    akten[str(member.id)]["jails"] += 1
    save("akten.json", akten)
    await ctx.send("🔒 Gejailt")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unjail(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="jailed")
    await member.remove_roles(role)
    await ctx.send("🔓 Entjailt")

@bot.command()
async def akte(ctx, member: discord.Member = None):
    member = member or ctx.author
    j = akten.get(str(member.id), {}).get("jails",0)
    w = len(warnings.get(str(member.id),[]))
    await ctx.send(f"📂 Akte\nJails: {j}\nWarns: {w}")

# ================== MARRY ==================
@bot.command()
async def marry(ctx, member: discord.Member):
    if str(ctx.author.id) in marriages:
        await ctx.send("❌ Schon verheiratet")
        return
    marriages[str(ctx.author.id)] = str(member.id)
    marriages[str(member.id)] = str(ctx.author.id)
    save("marriages.json", marriages)
    await ctx.send("💍 Verheiratet!")

@bot.command()
async def marrystatus(ctx):
    uid = str(ctx.author.id)
    if uid not in marriages:
        await ctx.send("💔 Nicht verheiratet")
        return
    partner = ctx.guild.get_member(int(marriages[uid]))
    await ctx.send(f"💞 Verheiratet mit {partner.mention}")

@bot.command()
async def divorce(ctx):
    uid = str(ctx.author.id)
    pid = marriages.get(uid)
    if not pid:
        return
    del marriages[uid]
    del marriages[pid]
    save("marriages.json", marriages)
    await ctx.send("💔 Geschieden")

# ================== TTT ==================
class TTT(View):
    def __init__(self, p1, p2):
        super().__init__(timeout=120)
        self.board = ["⬜"]*9
        self.turn = p1
        self.p1, self.p2 = p1, p2
        for i in range(9):
            self.add_item(TTTBtn(i, self))

class TTTBtn(Button):
    def __init__(self, i, game):
        super().__init__(label=" ", style=ButtonStyle.secondary, row=i//3)
        self.i, self.game = i, game

    async def callback(self, i):
        if i.user != self.game.turn:
            return
        sym = "❌" if self.game.turn == self.game.p1 else "⭕"
        self.label = sym
        self.disabled = True
        self.game.board[self.i] = sym
        self.game.turn = self.game.p2 if self.game.turn == self.game.p1 else self.game.p1
        await i.response.edit_message(view=self.game)

@bot.command()
async def ttt(ctx, member: discord.Member):
    await ctx.send("🎮 TicTacToe", view=TTT(ctx.author, member))

# ================== RUN ==================
bot.run(os.environ["TOKEN"])
