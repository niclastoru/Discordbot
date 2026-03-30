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

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Moderation", style=discord.ButtonStyle.red)
    async def mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛠️ Moderation",
            description="""
`?ban`
`?unban`
`?timeout`
`?role`
            """,
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="User", style=discord.ButtonStyle.blurple)
    async def user(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👤 User",
            description="""
`?avatar`
`?info`
`?stats`
            """,
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Fun", style=discord.ButtonStyle.green)
    async def fun(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎮 Fun",
            description="""
`?gayrate`
`?straight`
`?lesbian`
            """,
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=self)
        
@bot.event
async def on_ready():
    print(f"🔥 Bot online als {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📖 Help Menü",
        description="Wähle unten eine Kategorie 👇",
        color=discord.Color.blurple()
    )

    embed.add_field(name="🛠️ Moderation", value="Ban, Timeout...", inline=False)
    embed.add_field(name="👤 User", value="Avatar, Stats...", inline=False)
    embed.add_field(name="🎮 Fun", value="Fun Commands", inline=False)

    await ctx.send(embed=embed, view=HelpView())

bot.run(TOKEN)
