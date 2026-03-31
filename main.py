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
async def on_ready():
    print(f"🔥 Bot online als {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

bot.run(TOKEN)
