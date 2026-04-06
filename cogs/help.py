import discord
from discord.ext import commands

# ================= DROPDOWN =================
class HelpSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot

        options = []

        for cog_name, cog in bot.cogs.items():
            if cog_name == "Help":
                continue

            options.append(
                discord.SelectOption(
                    label=cog_name,
                    description=f"Commands in {cog_name}"
                )
            )

        super().__init__(
            placeholder="Select a category",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        cog_name = self.values[0]
        cog = self.bot.get_cog(cog_name)

        commands_list = cog.get_commands()

        text = ""
        for cmd in commands_list:
            text += f"`!{cmd.name}` - {cmd.help or 'No description'}\n"

        if text == "":
            text = "No commands found."

        embed = discord.Embed(
            title=f"📂 {cog_name}",
            description=text,
            color=discord.Color.blurple()
        )

        await interaction.response.edit_message(embed=embed, view=self.view)


# ================= VIEW =================
class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.add_item(HelpSelect(bot))


# ================= COG =================
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title="📖 Help Menu",
            description="Select a category below",
            color=discord.Color.blurple()
        )

        embed.set_footer(text=f"{len(self.bot.commands)} commands loaded")

        await ctx.send(embed=embed, view=HelpView(self.bot))


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Help(bot))
