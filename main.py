# ================= IMPORT =================
import discord
from discord.ext import commands
import os, json, time, random
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents, case_insensitive=True)

DATA_FILE = "data.json"

# ================= DATA =================

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

def get_guild(gid):
    gid = str(gid)
    if gid not in data:
        data[gid] = {
            "staff": [],
            "autoresponder": {},
            "stats": {}
        }
    return data[gid]

# ================= READY =================

@bot.event
async def on_ready():
    print(f"🔥 Jerry online als {bot.user}")

# ================= STAFF =================

def is_staff(member):
    guild = get_guild(member.guild.id)
    return any(r.id in guild["staff"] for r in member.roles)

@bot.command()
async def settings(ctx, action=None, role: discord.Role=None):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Keine Rechte")

    guild = get_guild(ctx.guild.id)

    if action == "add":
        guild["staff"].append(role.id)
        save_data()
        await ctx.send(f"✅ {role.mention} hinzugefügt")

    elif action == "remove":
        guild["staff"].remove(role.id)
        save_data()
        await ctx.send(f"🗑️ {role.mention} entfernt")

    elif action == "list":
        roles = [ctx.guild.get_role(r) for r in guild["staff"]]
        await ctx.send("\n".join(r.mention for r in roles if r) or "Keine")

# ================= HELP =================

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📖 Commands", color=discord.Color.blurple())

    for cmd in bot.commands:
        embed.add_field(
            name=f".{cmd.name}",
            value="Command verfügbar",
            inline=False
        )

    await ctx.send(embed=embed)

# ================= MOD =================

@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    if not is_staff(ctx.author): return await ctx.send("❌")
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member} gebannt")

@bot.command()
async def unban(ctx, user_id: int):
    if not is_staff(ctx.author): return
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"♻️ {user} entbannt")

@bot.command()
async def jail(ctx, member: discord.Member):
    if not is_staff(ctx.author): return
    role = discord.utils.get(ctx.guild.roles, name="jailed")
    if role:
        await member.add_roles(role)
        await ctx.send("🔒 gejailt")

@bot.command()
async def unjail(ctx, member: discord.Member):
    if not is_staff(ctx.author): return
    role = discord.utils.get(ctx.guild.roles, name="jailed")
    if role:
        await member.remove_roles(role)
        await ctx.send("🔓 entjailt")

@bot.command()
async def timeout(ctx, member: discord.Member, minutes: int):
    if not is_staff(ctx.author): return
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)
    await ctx.send("🔇 Timeout")

@bot.command()
async def untimeout(ctx, member: discord.Member):
    if not is_staff(ctx.author): return
    await member.timeout(None)
    await ctx.send("🔊 Timeout entfernt")

@bot.command(aliases=["clear","c"])
async def purge(ctx, amount: int):
    if not ctx.author.guild_permissions.manage_messages: return
    await ctx.channel.purge(limit=amount+1)

# ================= USER =================

@bot.command(aliases=["av"])
async def avatar(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
async def info(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(f"{member} | ID: {member.id}")

# ================= FUN =================

@bot.command()
async def gayrate(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(f"{member} ist {random.randint(0,100)}% gay 😈")

# ================= AUTORESPONDER =================

@bot.command()
async def ar_add(ctx, *, text):
    if not is_staff(ctx.author): return

    trigger, response = text.split("|",1)
    guild = get_guild(ctx.guild.id)

    guild["autoresponder"][trigger.lower()] = response
    save_data()

    await ctx.send("✅ gespeichert")

@bot.command()
async def ar_remove(ctx, trigger):
    if not is_staff(ctx.author): return
    guild = get_guild(ctx.guild.id)

    guild["autoresponder"].pop(trigger.lower(), None)
    save_data()

    await ctx.send("🗑️ gelöscht")

@bot.command()
async def ar_list(ctx):
    guild = get_guild(ctx.guild.id)
    await ctx.send(str(guild["autoresponder"]))

# ================= SNIPER =================

snipes = {}

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    snipes[message.channel.id] = (message.content, message.author, time.time())

@bot.command()
async def s(ctx):
    snipe = snipes.get(ctx.channel.id)
    if not snipe: return await ctx.send("❌")

    msg, author, t = snipe
    if time.time()-t > 7200:
        return await ctx.send("❌ zu alt")

    await ctx.send(f"{author}: {msg}")

# ================= STATS =================

@bot.event
async def on_message(message):
    if message.author.bot: return

    guild = get_guild(message.guild.id)
    user = str(message.author.id)

    now = datetime.utcnow().isoformat()

    if user not in guild["stats"]:
        guild["stats"][user] = {"messages":[]}

    guild["stats"][user]["messages"].append(now)

    # autoresponder
    if message.content.lower() in guild["autoresponder"]:
        await message.channel.send(guild["autoresponder"][message.content.lower()])

    if random.randint(1,5)==1:
        save_data()

    await bot.process_commands(message)

@bot.command()
async def stats(ctx, member: discord.Member=None):
    member = member or ctx.author
    guild = get_guild(ctx.guild.id)
    user = str(member.id)

    msgs = len(guild["stats"].get(user,{}).get("messages",[]))

    await ctx.send(f"📊 {member}: {msgs} Nachrichten")

# ================= START =================

bot.run(TOKEN)
