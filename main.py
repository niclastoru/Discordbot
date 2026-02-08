# ================== IMPORTS ==================
import discord
from discord.ext import commands
from discord.ui import View, button
from discord import ButtonStyle
import random, json, os, re
import datetime
import asyncio
import aiohttp
import io

LOG_CHANNEL_ID = 123456789012345678  # <-- Log-Channel-ID
CEO_ROLE_NAME = "CEO"                # <-- Rollenname

def is_protected(member: discord.Member):
    if member.guild_permissions.administrator:
        return True
    return any(role.name == CEO_ROLE_NAME for role in member.roles)
    
BARKEEPER_AD_TEXTS = [
    "🍸 Ich sag nur eins: Aus Dreck wird Dominanz.\nHier ist der Ort, wo man nicht redet – sondern liefert.\n\n👉 {link}",
    "Man landet nicht hier aus Zufall.\nWenn du Hunger hast auf mehr als nur Chat – komm rein.\n\n🔥 {link}",
    "Der Barkeeper serviert keine Ausreden.\nNur Bewegung, Stimme und Präsenz.\n\n🍷 {link}",
    "Manche bleiben unten.\nAndere bauen sich hoch.\nWir sind der zweite Typ.\n\n🚀 {link}",
    "Kein offizieller Invite.\nNur ein stiller Hinweis.\n\n👁️ {link}"
]

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

AFK_FILE = "afk.json"

def load_afk():
    if not os.path.exists(AFK_FILE):
        return {}
    with open(AFK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_afk(data):
    with open(AFK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

afk_users = load_afk()

GERUECHTE = [
    "Man sagt, er zahlt Drinks immer mit geliehenen Coins 🍺",
    "Hat angeblich schon mal aus Versehen den Barkeeper beleidigt 😬",
    "Niemand weiß, wo er war zwischen 02:00 und 03:00 Uhr…",
    "Bestellt immer Wasser, sagt aber es sei Wodka 👀",
    "Hat mehr Geheimnisse als die Akten im Keller 🗂️",
    "Tut unschuldig, aber kennt jede Hintertür 🚪",
    "Wurde schon mal flüsternd über ihn gesprochen…",
    "Kennt den Barkeeper angeblich *zu gut* 😏",
    "War schon öfter in Barfight verwickelt als er zugibt 💥",
    "Man munkelt… er ist gefährlicher als er aussieht 🔥"
]

SCHICKSAL_LISTE = [
    "🕯️ Wird Recht haben – aber niemand wird es zugeben.",
    "🍷 Wird sich über etwas aufregen, das er selbst verursacht hat.",
    "🪙 Wird heute Glück haben… leider nur bei unnützen Dingen.",
    "👁️ Jemand denkt öfter an diese Person, als sie glaubt.",
    "🕶️ Wird etwas Wichtiges vergessen – und es später dramatisieren.",
    "🔥 Hat mehr Einfluss, als er zugibt.",
    "🍺 Wird heute eine Entscheidung bereuen, aber dazu stehen.",
    "🌙 Die Nacht bringt Antworten – oder neue Fragen.",
    "🃏 Sollte heute besser nicht provozieren.",
    "🔒 Weiß ein Geheimnis, das noch wichtig wird."
]

BARKEEPER_LINES = [
    "🍺 Genug. Jetzt rede ich.",
    "👁️ Ich beobachte euch schon länger.",
    "💥 Manche sollten heute lieber still sein.",
    "🕯️ Dein Verhalten bleibt nicht unbemerkt.",
    "🥃 Setz dich. Wir müssen reden.",
    "🚬 Du bist heute auffälliger als du denkst.",
    "🧠 Sag weniger. Denk mehr."
]

class ChaosView(View):
    def __init__(self, author):
        super().__init__(timeout=30)
        self.author = author

    @button(label="🔥 CHAOS AUSLÖSEN", style=ButtonStyle.danger)
    async def chaos_button(self, interaction: discord.Interaction, btn):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "❌ Das ist **nicht** dein Chaos.",
                ephemeral=True
            )
            return

        outcomes = [
            "🍺 Der Barkeeper wirft dich raus.",
            "💰 Du findest **50 Coins** unter dem Tresen.",
            "💥 Barfight! Du verlierst **20 XP**.",
            "😳 Alle lachen. Peinlich.",
            "😇 Glück gehabt – nichts passiert.",
            "📝 Eine neue Aktennotiz wurde erstellt.",
            "🔥 Chaos eskaliert… aber du überlebst."
        ]

        result = random.choice(outcomes)

        await interaction.response.edit_message(
            content=f"🎲 **CHAOS AUSGELÖST**\n{result}",
            view=None
        )

PAST_LINES = [
    "Vor 5 Jahren: Ahnungslos, aber voller Hoffnung.",
    "Vor 5 Jahren: Zu gut für diese Welt.",
    "Vor 5 Jahren: Dachte, er hätte alles im Griff.",
    "Vor 5 Jahren: Schon damals gefährlich.",
    "Vor 5 Jahren: Hat Fehler gemacht – große."
]

FUTURE_LINES = [
    "In 5 Jahren: Mächtiger, als er jetzt denkt.",
    "In 5 Jahren: Reich, aber misstrauisch.",
    "In 5 Jahren: Gleicher Server, andere Rolle.",
    "In 5 Jahren: Alle kennen seinen Namen.",
    "In 5 Jahren: Hat alles erreicht – fast."
]
# ================== INTENTS ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

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
session = None
@bot.event
async def on_ready():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()

    print(f"✅ Online als {bot.user}")
# ================== LINK BLOCK ==================
DISCORD_INVITE_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?(?:discord\.gg|discord\.com\/invite)\/\w+",
    re.IGNORECASE
)

@bot.event
async def on_message(message):
    if not message.guild:
        return

    content = message.content.lower()

    # 🚨 DISCORD SERVERLINK → IMMER BLOCK
    if DISCORD_INVITE_REGEX.search(content):
        try:
            await message.delete()
        except:
            pass

        # Nur echte User bannen
        if not message.author.bot:
            try:
                await message.guild.ban(
                    message.author,
                    reason="Automatischer Bann: Discord-Serverlink"
                )
            except:
                pass

        return

    # 🔥 WEBHOOK KOMPLETT VERBOTEN
    if message.webhook_id is not None:
        try:
            await message.delete()
        except:
            pass
        return

    # 🤖 Bots ignorieren (nach Webhook-Check!)
    if message.author.bot:
        return

    uid = str(message.author.id)

    # ================= AFK REMOVE =================
    if uid in afk_users and not message.content.startswith(("!", "/")):
        del afk_users[uid]
        save("afk.json", afk_users)

        await message.channel.send(
            f"👋 Willkommen zurück {message.author.mention}, AFK entfernt.",
            delete_after=5
        )

    # 🔔 AFK-HINWEIS BEI ERWÄHNUNG
    for user in message.mentions:
        u_id = str(user.id)
        if u_id in afk_users:
            await message.channel.send(
                f"💤 **{user.display_name}** ist AFK\n📌 Grund: **{afk_users[u_id]['reason']}**",
                delete_after=5
            )
     
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

        if message.author.bot:
            return

    uid = str(message.author.id)

    import random
    
   # 🍸 Barkeeper greift selten ein
    import random
    if random.randint(1, 100) <= 4:  # 4% Chance
        embed = discord.Embed(
            title="🍸 Der Barkeeper spricht",
            description=random.choice(BARKEEPER_LINES),
            color=discord.Color.dark_gold()
        )
        
        embed.set_footer(text="Der Barkeeper hat eingegriffen")
        await message.channel.send(embed=embed)

    # ⚠️ GANZ WICHTIG
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
    add_history(member, "WARN", ctx.author, reason)
    

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

@bot.command()
@commands.has_permissions(administrator=True)
async def ar_add(ctx, *, text):
    if "|" not in text:
        await ctx.send("❌ Nutzung: ,ar_add trigger | antwort")
        return

    trigger, response = map(str.strip, text.split("|", 1))
    autoresponder[trigger.lower()] = response
    save_autoresponder(autoresponder)

    await ctx.send(f"✅ AutoResponder gespeichert für `{trigger}`")

@bot.command()
async def ar_list(ctx):
    if not autoresponder:
        await ctx.send("❌ Keine AutoResponder vorhanden")
        return

    text = "\n".join(f"- `{k}`" for k in autoresponder.keys())
    await ctx.send(f"🤖 **AutoResponder:**\n{text}")

@bot.command()
@commands.has_permissions(administrator=True)
async def ar_remove(ctx, *, trigger):
    trigger = trigger.lower()

    if trigger not in autoresponder:
        await ctx.send("❌ Trigger nicht gefunden")
        return

    del autoresponder[trigger]
    save_autoresponder(autoresponder)

    await ctx.send(f"🗑️ `{trigger}` gelöscht")

@bot.command()
async def afk(ctx, *, reason="AFK"):
    uid = str(ctx.author.id)

    afk_users[uid] = {
        "reason": reason,
        "time": int(discord.utils.utcnow().timestamp())
    }
    save_afk(afk_users)

    embed = discord.Embed(
        title="💤 AFK aktiviert",
        description=f"**Grund:** {reason}",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def rules(ctx):
    embed = discord.Embed(
        title=f"📜 {ctx.guild.name} Regelwerk",
        description="Bitte lies dir die Regeln sorgfältig durch.",
        color=discord.Color.dark_blue()
    )

    # ✅ Server Banner oben (wenn vorhanden)
    if ctx.guild.banner:
        embed.set_image(url=ctx.guild.banner.url)

    # ✅ Server Icon als Thumbnail
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)

    embed.add_field(
        name="🚫 Verboten",
        value=(
            "• kein leaking\n"
            "• kein doxxing\n"
            "• keine Werbung\n"
            "• kein spammen"
        ),
        inline=False
    )

    embed.add_field(
        name="⚖️ Allgemein",
        value="Respektvoller Umgang. Admin/Mod Anweisungen sind zu befolgen.",
        inline=False
    )

    embed.add_field(
        name="📘 Discord ToS",
        value="https://discord.com/terms",
        inline=False
    )

    embed.set_footer(text=f"Regelwerk • {ctx.guild.name}")

    await ctx.send(embed=embed)

# ================= FUN COMMANDS =================

@bot.command()
async def dice(ctx):
    n = random.randint(1,6)
    embed = discord.Embed(
        title="🎲 Würfel",
        description=f"Du hast eine **{n}** gewürfelt!",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)


@bot.command()
async def meme(ctx):
    memes = [
        "Ich nach 1 Commit: Senior Developer",
        "Code läuft → nicht anfassen",
        "Bug? Feature.",
        "Ich teste nur kurz — alles kaputt",
        "Deploy am Freitag = Mut"
    ]
    embed = discord.Embed(
        title="😂 Meme",
        description=random.choice(memes),
        color=discord.Color.random()
    )
    await ctx.send(embed=embed)


@bot.command()
async def roast(ctx, member: discord.Member):
    roasts = [
        "läuft bei dir wie Windows 95",
        "du bist kein Bug — du bist ein ganzes Update",
        "dein WLAN hat mehr Persönlichkeit",
        "sogar mein Bot hat mehr XP",
        "CPU auf Sparmodus bei dir"
    ]
    embed = discord.Embed(
        title="🔥 Roast",
        description=f"{member.mention} — {random.choice(roasts)}",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)


@bot.command()
async def kiss(ctx, member: discord.Member):
    embed = discord.Embed(
        title="💋 Kiss",
        description=f"{ctx.author.mention} küsst {member.mention}",
        color=discord.Color.pink()
    )
    await ctx.send(embed=embed)


@bot.command()
async def fight(ctx, member: discord.Member):
    winner = random.choice([ctx.author, member])
    embed = discord.Embed(
        title="🥊 Fight",
        description=f"{ctx.author.mention} vs {member.mention}\n\n🏆 Gewinner: {winner.mention}",
        color=discord.Color.dark_red()
    )
    await ctx.send(embed=embed)


@bot.command()
async def ball(ctx, *, frage):
    answers = [
        "Ja", "Nein", "Safe", "Unwahrscheinlich",
        "Frag später", "Definitiv", "Nope",
        "Sieht gut aus", "Keine Chance"
    ]
    embed = discord.Embed(
        title="🔮 8Ball",
        description=f"Frage: {frage}\nAntwort: **{random.choice(answers)}**",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)


@bot.command()
async def steal(ctx, member: discord.Member):
    if member.bot:
        return await ctx.send("❌ Von Bots klauen ist cringe")

    gain = random.randint(10,100)
    success = random.choice([True, False])

    if success:
        coins[str(ctx.author.id)] = coins.get(str(ctx.author.id),0) + gain
        coins[str(member.id)] = max(0, coins.get(str(member.id),0) - gain)
        save_json(COIN_FILE, coins)

        text = f"💸 Erfolgreich {gain} Coins von {member.mention} geklaut!"
        color = discord.Color.green()
    else:
        text = "🚨 Erwischt! Kein Coin bekommen."
        color = discord.Color.red()

    embed = discord.Embed(title="🕵️ Diebstahl", description=text, color=color)
    await ctx.send(embed=embed)

# ================== SERVER MOVE ==================

@bot.command()
@commands.has_permissions(administrator=True)
async def move(ctx, link):
    embed = discord.Embed(
        title="🚀 Server Umzug",
        description=(
            "Dieser Server zieht um!\n\n"
            f"👉 **Neuer Server:** {link}\n\n"
            "Bitte joint dort — dieser Server wird bald geschlossen."
        ),
        color=discord.Color.gold()
    )

    await ctx.send("@everyone", embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def move_dm(ctx, link):
    embed = discord.Embed(
        title="🚀 Server Umzug",
        description=(
            f"Dieser Server zieht um.\n\n"
            f"👉 Neuer Server: {link}\n\n"
            "Du bist eingeladen zu joinen!"
        ),
        color=discord.Color.gold()
    )

    sent = 0
    failed = 0

    msg = await ctx.send("📨 Starte DM Versand...")

    for member in ctx.guild.members:
        if member.bot:
            continue
        try:
            await member.send(embed=embed)
            sent += 1
        except:
            failed += 1

    await msg.edit(
        content=f"✅ Fertig.\nGesendet: {sent}\nFehlgeschlagen: {failed}"
    )

@bot.command()
async def drink(ctx, member: discord.Member = None):
    drinks = [
        ("🍺 Bier", "klassisch, kalt und ehrlich."),
        ("🍷 Wein", "edler Tropfen, ruhig genießen."),
        ("🥃 Whiskey", "stark. Direkt. Keine Fragen."),
        ("🍹 Cocktail", "süß, gefährlich – Barkeeper-Empfehlung."),
        ("🍸 Martini", "geschüttelt, nicht gerührt."),
        ("🧃 Saft", "für heute lieber ruhig 😇"),
        ("🔥 Shot", "oha… mutig."),
        ("☕ Kaffee", "kein Alkohol, aber nötig.")
    ]

    drink, text = random.choice(drinks)

    if member is None:
        target = ctx.author
        desc = f"{ctx.author.mention} bekommt von **Barkeeper** einen **{drink}**.\n\n_{text}_"
    else:
        target = member
        desc = (
            f"{ctx.author.mention} serviert {member.mention} einen **{drink}** 🍸\n\n"
            f"_Barkeeper sagt: {text}_"
        )

    embed = discord.Embed(
        title="🍸 Barkeeper serviert",
        description=desc,
        color=discord.Color.gold()
    )

    embed.set_footer(text="Barkeeper • Bitte verantwortungsvoll genießen")
    embed.set_thumbnail(url=target.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def barfight(ctx, member: discord.Member):
    if member.bot or member == ctx.author:
        await ctx.send("❌ Der Barkeeper kämpft nicht gegen Bots oder sich selbst.")
        return

    moves = [
        "wirft ein Bierglas 🍺",
        "haut mit dem Barhocker 🪑 zu",
        "schlägt mit einer Whiskyflasche 🥃",
        "verpasst einen üblen Kinnhaken 🤜",
        "rutscht aus und tritt trotzdem 😭",
        "zieht einen Überraschungs-Uppercut ⚡"
    ]

    winner = random.choice([ctx.author, member])
    loser = member if winner == ctx.author else ctx.author
    move = random.choice(moves)

    embed = discord.Embed(
        title="🥊 BARFIGHT IM KIEZ 🍻",
        description=(
            f"🔥 **{ctx.author.display_name}** vs **{member.display_name}**\n\n"
            f"💥 **{winner.mention}** {move}\n"
            f"☠️ **{loser.mention}** geht zu Boden!\n\n"
            f"🍺 Der Barkeeper wischt das Blut weg."
        ),
        color=discord.Color.red()
    )

    embed.set_footer(text="Barkeeper sagt: Keine Schlägereien… außer diese 😏")

    await ctx.send(embed=embed)

@bot.command()
async def gerücht(ctx, member: discord.Member = None):
    member = member or ctx.author

    geruecht = random.choice(GERUECHTE)

    embed = discord.Embed(
        title="🗣️ Gerücht aus der Bar",
        description=(
            f"👤 **Über:** {member.mention}\n\n"
            f"🍸 *{geruecht}*"
        ),
        color=discord.Color.dark_gold()
    )

    embed.set_footer(
        text=f"Gerücht serviert von Barkeeper 🍺 | Angefordert von {ctx.author}",
        icon_url=ctx.author.display_avatar.url
    )

    await ctx.send(embed=embed)

@bot.command()
async def detektor(ctx):
    async for msg in ctx.channel.history(limit=10):
        if msg.author.bot or msg.author == ctx.author:
            continue

        target_msg = msg
        break
    else:
        await ctx.send("❌ Keine passende Aussage gefunden.")
        return

    result = random.choice(["truth", "lie", "unknown"])

    if result == "truth":
        title = "🟢 Wahrheits-Detektor"
        text = "Der Barkeeper nickt langsam…\n\n**Das klingt ehrlich.** 🧠✨"
        color = discord.Color.green()

    elif result == "lie":
        title = "🔴 Lügen-Detektor"
        text = "Der Barkeeper verengt die Augen…\n\n**Das ist gelogen.** 😈🔥"
        color = discord.Color.red()

    else:
        title = "🟡 Detektor unsicher"
        text = "Der Barkeeper zuckt mit den Schultern…\n\n**Nicht eindeutig.** 🤨"
        color = discord.Color.gold()

    embed = discord.Embed(
        title=title,
        description=(
            f"👤 **Person:** {target_msg.author.mention}\n"
            f"💬 **Aussage:**\n> {target_msg.content}\n\n"
            f"{text}"
        ),
        color=color
    )

    embed.set_footer(text=f"Detektor aktiviert von {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
async def schicksal(ctx, member: discord.Member = None):
    member = member or ctx.author
    prophecy = random.choice(SCHICKSAL_LISTE)

    embed = discord.Embed(
        title="🔮 Das Schicksal hat gesprochen",
        description=f"**{member.display_name}**\n\n{prophecy}",
        color=discord.Color.dark_purple()
    )

    embed.set_footer(text="Der Barkeeper irrt sich nie 🍺")
    embed.set_thumbnail(url=member.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def barkeeper(ctx):
    members = [m for m in ctx.guild.members if not m.bot]

    if not members:
        await ctx.send("🍺 Heute ist niemand hier.")
        return

    target = random.choice(members)

    embed = discord.Embed(
        title="🍸 Der Barkeeper greift ein",
        description=(
            f"👁️ **{target.mention}**\n\n"
            f"{random.choice(BARKEEPER_LINES)}"
        ),
        color=discord.Color.dark_red()
    )
    embed.set_footer(text=f"Ausgelöst von {ctx.author}")

    await ctx.send(embed=embed)

@bot.event
async def on_member_join(member):
    role_name = ".gg/treppenhaus"
    role = discord.utils.get(member.guild.roles, name=role_name)

    if role:
        try:
            await member.add_roles(role)
            print(f"{member} hat automatisch die Rolle {role_name} bekommen")
        except Exception as e:
            print(f"Fehler beim Rollen geben: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def givekiez(ctx):
    role_name = ".gg/dckiez"
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if not role:
        await ctx.send("❌ Rolle `.gg/treppenhaus` wurde nicht gefunden.")
        return

    added = 0
    skipped = 0

    msg = await ctx.send("🔄 Verteile Rollen...")

    for member in ctx.guild.members:
        if member.bot:
            continue
        if role in member.roles:
            skipped += 1
            continue
        try:
            await member.add_roles(role)
            added += 1
        except:
            pass

    await msg.edit(
        content=(
            f"✅ **Fertig!**\n"
            f"👤 Neu vergeben: **{added}**\n"
            f"⏭️ Schon vorhanden: **{skipped}**"
        )
    )
@bot.command()
async def chaos(ctx):
    await ctx.send(
        "😈 **Willkommen im Chaos**\nDrück den Button, wenn du dich traust.",
        view=ChaosView(ctx.author)
    )

@bot.command()
async def zeitreise(ctx):
    direction = random.choice(["past", "future"])

    if direction == "past":
        text = random.choice(PAST_LINES)
        title = "🕰️ Zeitreise – Vergangenheit"
        color = discord.Color.dark_blue()
    else:
        text = random.choice(FUTURE_LINES)
        title = "🔮 Zeitreise – Zukunft"
        color = discord.Color.dark_purple()

    embed = discord.Embed(
        title=title,
        description=text,
        color=color
    )
    embed.set_footer(text=f"Zeitreise ausgelöst von {ctx.author.display_name}")

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def barkeeperdm(ctx, link: str):
    embed = discord.Embed(
        title="🍸 Nachricht vom Barkeeper",
        description=random.choice(BARKEEPER_AD_TEXTS).format(link=link),
        color=discord.Color.dark_gold()
    )
    embed.set_footer(text="Aus Dreck zu Dominanz")

    sent = 0
    failed = 0

    status_msg = await ctx.send("📨 Barkeeper verteilt Drinks per DM…")

    for member in ctx.guild.members:
        if member.bot:
            continue
        try:
            await member.send(embed=embed)
            sent += 1
            await asyncio.sleep(1.5)  # WICHTIG gegen Rate-Limit
        except:
            failed += 1

    await status_msg.edit(
        content=(
            "🍾 **FERTIG**\n"
            f"✅ Gesendet: **{sent}**\n"
            f"❌ Fehlgeschlagen: **{failed}**"
        )
    )

@bot.event
async def on_guild_role_update(before, after):
    guild = after.guild

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
        user = entry.user

        if user.bot:
            return

        member = guild.get_member(user.id)
        if not member:
            return

        # ✅ Ausnahmen
        if member.guild_permissions.administrator:
            return

        if any(role.name.lower() == "ceo" for role in member.roles):
            return

        # ❌ Kick
        try:
            await member.kick(reason="Unbefugtes Bearbeiten von Rollen")
            await guild.system_channel.send(
                f"🚨 **Sicherheitskick**\n"
                f"👤 {member.mention}\n"
                f"🛑 Grund: Rollen bearbeitet"
            )
        except:
            pass

@bot.event
async def on_guild_role_delete(role):
    guild = role.guild

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        user = entry.user

        if user.bot:
            return

        member = guild.get_member(user.id)
        if not member:
            return

        # ✅ Ausnahmen
        if member.guild_permissions.administrator:
            return

        if any(r.name.lower() == "ceo" for r in member.roles):
            return

        # ❌ Kick
        try:
            await member.kick(reason="Unbefugtes Löschen einer Rolle")
            await guild.system_channel.send(
                f"🚨 **Sicherheitskick**\n"
                f"👤 {member.mention}\n"
                f"🛑 Grund: Rolle gelöscht"
            )
        except:
            pass

@bot.command()
async def chat(ctx):
    channel = ctx.channel

    active_members = [
        m for m in channel.members
        if not m.bot and m.status != discord.Status.offline
    ]

    count = len(active_members)

    embed = discord.Embed(
        title="💬 Chat-Aktivität",
        description=f"Es sind aktuell **{count} Personen** im Chat.",
        color=discord.Color.dark_gold()
    )

    # Aktive Namen (max. 5)
    names = ", ".join(m.display_name for m in active_members[:5])
    embed.add_field(
        name="👥 Aktiv",
        value=names if names else "Niemand gerade",
        inline=False
    )

    # Barkeeper Kommentar
    import random
    lines = [
        "🍸 Ruhiger Moment.",
        "🔥 Gespräche laufen.",
        "👀 Bewegung im Chat.",
        "🧠 Stimmen sind wach."
    ]

    embed.add_field(
        name="🍺 Barkeeper",
        value=random.choice(lines),
        inline=False
    )

    embed.set_footer(text="Live-Zählung")
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_emojis_and_stickers=True)
async def stickerclone(ctx):
    if not ctx.message.reference:
        await ctx.send("❌ Antworte auf eine Nachricht mit einem Sticker.")
        return

    ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    if not ref.stickers:
        await ctx.send("❌ In der Nachricht ist kein Sticker.")
        return

    sticker = ref.stickers[0]

    async with aiohttp.ClientSession() as session:
        async with session.get(sticker.url) as resp:
            if resp.status != 200:
                await ctx.send("❌ Sticker konnte nicht geladen werden.")
                return
            data = await resp.read()

    file = discord.File(fp=io.BytesIO(data), filename="sticker.png")

    try:
        await ctx.guild.create_sticker(
            name=sticker.name,
            description="Geklont über Barkeeper 🍸",
            emoji="🔥",
            file=file,
            reason=f"Sticker geklont von {ctx.author}"
        )

        await ctx.send(f"✅ Sticker **{sticker.name}** wurde geklont.")

    except Exception as e:
        await ctx.send(f"❌ Fehler: `{e}`")
        
@bot.event
async def on_close():
    if not session.closed:
        await session.close()
# ================== RUN ==================
bot.run(os.environ["TOKEN"])
