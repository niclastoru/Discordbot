import discord
from discord.ext import commands
import os
import re
from datetime import timedelta

def parse_time(time_str):
    time_str = time_str.lower().replace(" ", "")

    match = re.match(r"(\d+)([smhd]?)", time_str)
    if not match:
        return None

    value, unit = match.groups()
    value = int(value)

    if unit == "s":
        return timedelta(seconds=value)
    elif unit == "m" or unit == "":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)

    return None

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="?",
    intents=intents,
    case_insensitive=True,
    help_command=None
)

class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Moderation", description="Ban, Timeout etc."),
            discord.SelectOption(label="User", description="Avatar, Info etc."),
            discord.SelectOption(label="Fun", description="Fun Commands"),
            discord.SelectOption(label="System", description="Settings, Sniper etc.")
        ]

        super().__init__(
            placeholder="Wähle ein Modul",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]

        if choice == "Moderation":
            embed = discord.Embed(
                title="🛠️ Moderation",
                description="""
`?ban`
`?unban`
`?timeout`
`?untimeout`
`?role`
`?purge`
                """,
                color=discord.Color.red()
            )

        elif choice == "User":
            embed = discord.Embed(
                title="👤 User",
                description="""
`?avatar`
`?banner`
`?info`
`?stats`
                """,
                color=discord.Color.blurple()
            )

        elif choice == "Fun":
            embed = discord.Embed(
                title="🎮 Fun",
                description="""
`?gayrate`
`?straight`
`?lesbian`
                """,
                color=discord.Color.green()
            )

        elif choice == "System":
            embed = discord.Embed(
                title="⚙️ System",
                description="""
`?settings`
`?ar_add`
`?ar_remove`
`?ar_list`
`?s`
`?cs`
                """,
                color=discord.Color.dark_grey()
            )

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpDropdown())


@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📖 Jerry Help",
        description="""
Prefix: `?`

Wähle unten ein Modul aus,
um alle Commands zu sehen.
        """,
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed, view=HelpView())

@bot.event
async def on_command_error(ctx, error):

    # ❌ Keine Rechte
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Keine Rechte",
            description="Du darfst diesen Command nicht nutzen.",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    # ⚠️ Falsche Nutzung (z.B. Argument fehlt)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="⚠️ Falsche Nutzung",
            description=f"Nutze den Command so:\n`?{ctx.command} {ctx.command.signature}`",
            color=discord.Color.orange()
        )
        return await ctx.send(embed=embed)

    # ❌ Falscher Input
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="❌ Ungültige Eingabe",
            description="Bitte überprüfe deine Eingabe.",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    # ❌ Command existiert nicht
    elif isinstance(error, commands.CommandNotFound):
        return

    # 💥 Sonstige Errors (Debug)
    else:
        print(error)
        
@bot.event
async def on_ready():
    print(f"🔥 Bot online als {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, user_input: str, *, reason="Kein Grund angegeben"):

    user = None

    # 🔹 Versuch als Mention / Member
    if ctx.message.mentions:
        user = ctx.message.mentions[0]

    # 🔹 Versuch als ID
    else:
        try:
            user = await bot.fetch_user(int(user_input))
        except:
            return await ctx.send("❌ Ungültiger User oder ID")

    # 🔹 DM schicken
    try:
        await user.send(f"🔨 Du wurdest gebannt\nServer: {ctx.guild.name}\nGrund: {reason}")
    except:
        pass

    # 🔹 Ban
    try:
        await ctx.guild.ban(user, reason=reason)
    except Exception as e:
        return await ctx.send(f"❌ Fehler: {e}")

    embed = discord.Embed(
        title="🔨 User gebannt",
        description=f"{user} wurde gebannt\nGrund: {reason}",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):

    try:
        user = await bot.fetch_user(user_id)
    except:
        return await ctx.send("❌ Ungültige User ID")

    try:
        await ctx.guild.unban(user)
    except:
        return await ctx.send("❌ User ist nicht gebannt")

    embed = discord.Embed(
        title="♻️ User entbannt",
        description=f"{user} wurde entbannt",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, user_input: str, time: str):

    member = None

    # 🔹 Mention check
    if ctx.message.mentions:
        member = ctx.message.mentions[0]

    # 🔹 ID check
    else:
        try:
            member = await ctx.guild.fetch_member(int(user_input))
        except:
            return await ctx.send("❌ User nicht im Server")

    duration = parse_time(time)

    if not duration:
        return await ctx.send(embed=discord.Embed(
            title="❌ Ungültige Zeit",
            description="Beispiele:\n`?timeout @user 10m`\n`?timeout @user 2h`\n`?timeout @user 1d`",
            color=discord.Color.red()
        ))

    until = discord.utils.utcnow() + duration

    await member.timeout(until)

    embed = discord.Embed(
        title="🔇 Timeout",
        description=f"{member.mention} wurde getimeoutet\nDauer: `{time}`",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, user_input: str):

    member = None

    # 🔹 Mention
    if ctx.message.mentions:
        member = ctx.message.mentions[0]

    # 🔹 ID
    else:
        try:
            member = await ctx.guild.fetch_member(int(user_input))
        except:
            return await ctx.send("❌ User nicht im Server")

    try:
        await member.timeout(None)
    except:
        return await ctx.send("❌ Fehler beim Entfernen des Timeouts")

    embed = discord.Embed(
        title="🔊 Timeout entfernt",
        description=f"{member.mention} ist wieder frei",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

bot.run(TOKEN)
