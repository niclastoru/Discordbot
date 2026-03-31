import discord
from discord.ext import commands
import os

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
async def ban(ctx, member: discord.Member, *, reason="Kein Grund angegeben"):
    try:
        await member.send(f"🔨 Du wurdest gebannt\nServer: {ctx.guild.name}\nGrund: {reason}")
    except:
        pass

    await member.ban(reason=reason)

    embed = discord.Embed(
        title="🔨 User gebannt",
        description=f"{member.mention} wurde gebannt\nGrund: {reason}",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

    embed = discord.Embed(
        title="♻️ User entbannt",
        description=f"{user} wurde entbannt",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int):
    duration = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(duration)

    embed = discord.Embed(
        title="🔇 Timeout",
        description=f"{member.mention} für {minutes} Minuten",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None)

    embed = discord.Embed(
        title="🔊 Timeout entfernt",
        description=f"{member.mention} ist wieder frei",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

bot.run(TOKEN)
