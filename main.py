import discord
from discord.ext import commands
import os
import json
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="_", intents=intents, case_insensitive=True)

# ================= FILES =================

STAFF_FILE = "staff.json"

def load_staff():
    try:
        with open(STAFF_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_staff(data):
    with open(STAFF_FILE, "w") as f:
        json.dump(data, f)

staff_roles = load_staff()

from datetime import datetime, timedelta

STATS_FILE = "stats.json"

def load_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f)

stats_data = load_stats()

def create_stats_image(member, m1, m7, m14, v1, v7, v14):

    width, height = 1100, 600
    img = Image.new("RGB", (width, height), (14, 15, 18))
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.truetype("Inter_24pt-Bold.ttf", 32)
    font_big = ImageFont.truetype("Inter_24pt-Regular.ttf", 22)
    font_small = ImageFont.truetype("Inter_24pt-Regular.ttf", 16)

    def box(x, y, w, h):
        draw.rounded_rectangle((x, y, x+w, y+h), radius=20, fill=(30,30,35))

    # Avatar
    response = requests.get(member.display_avatar.url)
    avatar = Image.open(BytesIO(response.content)).resize((80, 80))
    img.paste(avatar, (40, 40))

    # Name
    draw.text((140, 60), str(member), fill=(255,255,255), font=font_title)

    # BOXEN
    box(40, 150, 300, 170)   # Server
    box(380, 150, 300, 170)  # Messages
    box(720, 150, 300, 170)  # Voice

    # TITLES
    draw.text((60, 170), "Server Stats", fill=(180,180,180), font=font_small)
    draw.text((400, 170), "Messages", fill=(180,180,180), font=font_small)
    draw.text((740, 170), "Voice Activity", fill=(180,180,180), font=font_small)

    # MESSAGES
    draw.text((400, 210), f"1d  {m1}", fill=(255,255,255), font=font_big)
    draw.text((400, 240), f"7d  {m7}", fill=(255,255,255), font=font_big)
    draw.text((400, 270), f"14d {m14}", fill=(255,255,255), font=font_big)

    # VOICE
    draw.text((740, 210), f"1d  {v1}h", fill=(255,255,255), font=font_big)
    draw.text((740, 240), f"7d  {v7}h", fill=(255,255,255), font=font_big)
    draw.text((740, 270), f"14d {v14}h", fill=(255,255,255), font=font_big)

    path = f"stats_{member.id}.png"
    img.save(path)
    return path

# ================= READY =================

@bot.event
async def on_ready():
    print(f"🔥 Jerry ist online als {bot.user}")

# ================= STAFF CHECK =================

def is_staff(member, guild):
    guild_id = str(guild.id)
    if guild_id not in staff_roles:
        return False
    return any(role.id in staff_roles[guild_id] for role in member.roles)

# ================= ERROR HANDLER =================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            description="Du hast keine Rechte um diesen Command zu nutzen.",
            color=discord.Color.red()
        ))

    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(embed=discord.Embed(
            title="⚠️ Falsche Nutzung",
            description=f"Nutze den Command richtig: `{ctx.prefix}{ctx.command} ...`",
            color=discord.Color.orange()
        ))

    if isinstance(error, commands.BadArgument):
        return await ctx.send(embed=discord.Embed(
            title="❌ Fehler",
            description="Ungültige Eingabe.",
            color=discord.Color.red()
        ))

# ================= SETTINGS =================

@bot.command()
async def settings(ctx, category: str, action: str = None, role: discord.Role = None):

    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            description="Du hast keine Rechte um diesen Command zu nutzen.",
            color=discord.Color.red()
        ))

    if category.lower() != "staff":
        return

    guild_id = str(ctx.guild.id)

    if guild_id not in staff_roles:
        staff_roles[guild_id] = []

    if action == "add" and role:
        if role.id not in staff_roles[guild_id]:
            staff_roles[guild_id].append(role.id)
            save_staff(staff_roles)

            return await ctx.send(embed=discord.Embed(
                title="✅ Rolle hinzugefügt",
                description=f"{role.mention} wurde gespeichert.",
                color=discord.Color.green()
            ))

    if action == "remove" and role:
        if role.id in staff_roles[guild_id]:
            staff_roles[guild_id].remove(role.id)
            save_staff(staff_roles)

            return await ctx.send(embed=discord.Embed(
                title="🗑️ Rolle entfernt",
                description=f"{role.mention} wurde entfernt.",
                color=discord.Color.orange()
            ))

    if action == "list":
        roles = [ctx.guild.get_role(r) for r in staff_roles[guild_id]]
        desc = "\n".join([r.mention for r in roles if r]) or "Keine Rollen gesetzt."

        return await ctx.send(embed=discord.Embed(
            title="📋 Staff Rollen",
            description=desc,
            color=discord.Color.blue()
        ))

# ================= ROLE =================

@bot.command(aliases=["r"])
async def role(ctx, member: discord.Member, *, role_name: str):

    if not is_staff(ctx.author, ctx.guild):
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            description="Du hast keine Rechte um diesen Command zu nutzen.",
            color=discord.Color.red()
        ))

    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if not role:
        return await ctx.send(embed=discord.Embed(
            title="❌ Fehler",
            description="Rolle nicht gefunden.",
            color=discord.Color.red()
        ))

    if role in member.roles:
        await member.remove_roles(role)
        title = "🗑️ Rolle entfernt"
        desc = f"{role.mention} entfernt von {member.mention}"
        color = discord.Color.orange()
    else:
        await member.add_roles(role)
        title = "✅ Rolle hinzugefügt"
        desc = f"{member.mention} hat jetzt {role.mention}"
        color = discord.Color.green()

    await ctx.send(embed=discord.Embed(title=title, description=desc, color=color))

# ================= JAIL =================

@bot.command()
async def jail(ctx, member: discord.Member):

    if not is_staff(ctx.author, ctx.guild):
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            color=discord.Color.red()
        ))

    role = discord.utils.get(ctx.guild.roles, name="jailed")

    if not role:
        return await ctx.send(embed=discord.Embed(
            title="❌ Fehler",
            description="Rolle 'jailed' existiert nicht.",
            color=discord.Color.red()
        ))

    await member.add_roles(role)

    try:
        await member.send(embed=discord.Embed(
            title="🔒 Du wurdest gejailt",
            description=f"Server: {ctx.guild.name}",
            color=discord.Color.dark_red()
        ))
    except:
        pass

    await ctx.send(embed=discord.Embed(
        title="🔒 User gejailt",
        description=f"{member.mention} wurde gejailt",
        color=discord.Color.dark_red()
    ))

@bot.command()
async def unjail(ctx, member: discord.Member):

    if not is_staff(ctx.author, ctx.guild):
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            color=discord.Color.red()
        ))

    role = discord.utils.get(ctx.guild.roles, name="jailed")

    if role in member.roles:
        await member.remove_roles(role)

    try:
        await member.send(embed=discord.Embed(
            title="🔓 Du wurdest entjailt",
            description=f"Server: {ctx.guild.name}",
            color=discord.Color.green()
        ))
    except:
        pass

    await ctx.send(embed=discord.Embed(
        title="🔓 User entjailt",
        description=f"{member.mention} ist frei",
        color=discord.Color.green()
    ))
    
# ================= BAN =================

@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):

    if not is_staff(ctx.author, ctx.guild):
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            color=discord.Color.red()
        ))

    try:
        await member.send(embed=discord.Embed(
            title="🔨 Du wurdest gebannt",
            description=f"Grund: {reason}",
            color=discord.Color.red()
        ))
    except:
        pass

    await member.ban(reason=reason)

    await ctx.send(embed=discord.Embed(
        title="🔨 User gebannt",
        description=f"{member.mention} wurde gebannt",
        color=discord.Color.red()
    ))

@bot.command()
async def unban(ctx, user_id: int):

    if not is_staff(ctx.author, ctx.guild):
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            color=discord.Color.red()
        ))

    user = await bot.fetch_user(user_id)

    await ctx.guild.unban(user)

    await ctx.send(embed=discord.Embed(
        title="♻️ User entbannt",
        description=f"{user} wurde entbannt",
        color=discord.Color.green()
    ))
    
# ================= TIMEOUT =================

@bot.command()
async def timeout(ctx, member: discord.Member, minutes: int):

    if not is_staff(ctx.author, ctx.guild):
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            color=discord.Color.red()
        ))

    duration = discord.utils.utcnow() + timedelta(minutes=minutes)

    await member.timeout(duration)

    try:
        await member.send(embed=discord.Embed(
            title="🔇 Timeout",
            description=f"{minutes} Minuten",
            color=discord.Color.orange()
        ))
    except:
        pass

    await ctx.send(embed=discord.Embed(
        title="🔇 Timeout gesetzt",
        description=f"{member.mention} für {minutes} Minuten",
        color=discord.Color.orange()
    ))

@bot.command()
async def untimeout(ctx, member: discord.Member):

    if not is_staff(ctx.author, ctx.guild):
        return await ctx.send(embed=discord.Embed(
            title="❌ Keine Rechte",
            color=discord.Color.red()
        ))

    await member.timeout(None)

    await ctx.send(embed=discord.Embed(
        title="🔊 Timeout entfernt",
        description=f"{member.mention} ist frei",
        color=discord.Color.green()
    ))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)
    now = datetime.utcnow().isoformat()

    if guild_id not in stats_data:
        stats_data[guild_id] = {}

    if user_id not in stats_data[guild_id]:
        stats_data[guild_id][user_id] = {
            "messages": []
        }

    stats_data[guild_id][user_id]["messages"].append(now)
    save_stats(stats_data)

    await bot.process_commands(message)

voice_times = {}

@bot.event
async def on_voice_state_update(member, before, after):

    guild_id = str(member.guild.id)
    user_id = str(member.id)

    # JOIN
    if not before.channel and after.channel:
        voice_times[user_id] = datetime.utcnow()

    # LEAVE
    if before.channel and not after.channel:
        if user_id in voice_times:
            start = voice_times.pop(user_id)
            duration = (datetime.utcnow() - start).total_seconds()

            if guild_id not in stats_data:
                stats_data[guild_id] = {}

            if user_id not in stats_data[guild_id]:
                stats_data[guild_id][user_id] = {
                    "messages": [],
                    "voice": []
                }

            if "voice" not in stats_data[guild_id][user_id]:
                stats_data[guild_id][user_id]["voice"] = []

            stats_data[guild_id][user_id]["voice"].append({
                "time": datetime.utcnow().isoformat(),
                "duration": duration
            })

            save_stats(stats_data)

@bot.command()
async def stats(ctx, member: discord.Member = None):

    member = member or ctx.author

    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    now = datetime.utcnow()

    messages = stats_data.get(guild_id, {}).get(user_id, {}).get("messages", [])
    voice = stats_data.get(guild_id, {}).get(user_id, {}).get("voice", [])

    def count_messages(days):
        return len([m for m in messages if datetime.fromisoformat(m) > now - timedelta(days=days)])

    def count_voice(days):
        total = 0
        for v in voice:
            if datetime.fromisoformat(v["time"]) > now - timedelta(days=days):
                total += v["duration"]
        return round(total / 3600, 2)

    m1, m7, m14 = count_messages(1), count_messages(7), count_messages(14)
    v1, v7, v14 = count_voice(1), count_voice(7), count_voice(14)

    path = create_stats_image(member, m1, m7, m14, v1, v7, v14)

    await ctx.send(file=discord.File(path))

@bot.command(aliases=["av"])
async def avatar(ctx, member: discord.Member = None):

    member = member or ctx.author

    embed = discord.Embed(
        title=f"🖼️ Avatar von {member}",
        color=discord.Color.blurple()
    )

    embed.set_image(url=member.display_avatar.url)
    embed.set_footer(text=f"ID: {member.id}")

    await ctx.send(embed=embed)

@bot.command()
async def banner(ctx, member: discord.Member = None):

    member = member or ctx.author

    user = await bot.fetch_user(member.id)

    if user.banner:
        embed = discord.Embed(
            title=f"🎨 Banner von {member}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=user.banner.url)
    else:
        embed = discord.Embed(
            title="❌ Kein Banner",
            description=f"{member} hat kein Banner.",
            color=discord.Color.red()
        )

    await ctx.send(embed=embed)
# ================= START =================

bot.run(TOKEN)
