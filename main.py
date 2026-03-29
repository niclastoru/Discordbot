import discord
from discord.ext import commands
import os
import json
from datetime import timedelta

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

# ================= START =================

bot.run(TOKEN)
