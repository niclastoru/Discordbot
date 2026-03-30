import discord
from discord.ext import commands
import os
import json
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import random
import time

# ================= BASIC =================

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents, case_insensitive=True, help_command=None)

sniped_messages = {}
SNIPER_TIMEOUT = 7200

# ================= FILE SYSTEM =================

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

staff_roles = load_json("staff.json")
stats_data = load_json("stats.json")
autoresponder = load_json("autoresponder.json")

# ================= HELP SYSTEM =================

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Moderation", style=discord.ButtonStyle.red)
    async def mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=discord.Embed(
            title="🛠️ Moderation",
            description="`?ban ?unban ?timeout ?untimeout ?jail ?unjail ?role ?purge`",
            color=discord.Color.red()
        ), view=self)

    @discord.ui.button(label="User", style=discord.ButtonStyle.blurple)
    async def user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=discord.Embed(
            title="👤 User",
            description="`?avatar ?banner ?info ?stats`",
            color=discord.Color.blurple()
        ), view=self)

    @discord.ui.button(label="Fun", style=discord.ButtonStyle.green)
    async def fun(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=discord.Embed(
            title="🎮 Fun",
            description="`?gayrate ?straight ?lesbian`",
            color=discord.Color.green()
        ), view=self)

    @discord.ui.button(label="System", style=discord.ButtonStyle.grey)
    async def system(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=discord.Embed(
            title="⚙️ System",
            description="`?settings ?ar_add ?ar_remove ?ar_list ?s ?cs`",
            color=discord.Color.dark_grey()
        ), view=self)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📖 Jerry Help", description="Wähle Kategorie 👇", color=discord.Color.blurple())
    await ctx.send(embed=embed, view=HelpView())

# ================= READY =================

@bot.event
async def on_ready():
    print(f"🔥 Online als {bot.user}")

# ================= STAFF CHECK =================

def is_staff(member):
    guild_id = str(member.guild.id)
    return any(role.id in staff_roles.get(guild_id, []) for role in member.roles)

# ================= EVENTS =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    gid = str(message.guild.id)
    uid = str(message.author.id)

    stats_data.setdefault(gid, {}).setdefault(uid, {"messages": []})
    stats_data[gid][uid]["messages"].append(datetime.utcnow().isoformat())
    save_json("stats.json", stats_data)

    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "time": time.time()
    }

# ================= MODERATION =================

@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    if not is_staff(ctx.author): return
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member} gebannt")

@bot.command()
async def unban(ctx, user_id: int):
    if not is_staff(ctx.author): return
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"♻️ {user} entbannt")

@bot.command()
async def timeout(ctx, member: discord.Member, minutes: int):
    if not is_staff(ctx.author): return
    await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes))
    await ctx.send(f"🔇 {member} Timeout {minutes}m")

@bot.command()
async def untimeout(ctx, member: discord.Member):
    if not is_staff(ctx.author): return
    await member.timeout(None)
    await ctx.send(f"🔊 {member} frei")

@bot.command(aliases=["clear","c"])
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"🧹 {amount} gelöscht", delete_after=5)

# ================= USER =================

@bot.command()
async def avatar(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
async def info(ctx, member: discord.Member=None):
    member = member or ctx.author
    embed = discord.Embed(title=str(member))
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

# ================= FUN =================

@bot.command()
async def gayrate(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(f"{member} ist {random.randint(0,100)}% gay 😈")

@bot.command()
async def straight(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(f"{member} ist {random.randint(0,100)}% straight")

@bot.command()
async def lesbian(ctx, member: discord.Member=None):
    member = member or ctx.author
    await ctx.send(f"{member} ist {random.randint(0,100)}% lesbian")

# ================= SNIPER =================

@bot.command()
async def s(ctx):
    data = sniped_messages.get(ctx.channel.id)
    if not data or time.time()-data["time"]>SNIPER_TIMEOUT:
        return await ctx.send("❌ Keine Daten")
    await ctx.send(f"{data['author']}: {data['content']}")

@bot.command()
async def cs(ctx):
    sniped_messages.pop(ctx.channel.id, None)
    await ctx.send("🧹 gelöscht")

# ================= START =================

bot.run(TOKEN)
