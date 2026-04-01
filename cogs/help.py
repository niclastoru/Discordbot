import discord
from discord.ext import commands

class HelpDropdown(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot

        categories = {}

        for command in bot.commands:
            cog = command.cog_name or "General"
            categories.setdefault(cog, []).append(command)

        self.categories = categories

        options = [
            discord.SelectOption(label=name, description=f"{len(cmds)} commands")
            for name, cmds in categories.items()
        ]

        super().__init__(
            placeholder="Select a category",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        commands_list = self.categories[category]

        desc = ""
        for cmd in commands_list:
            desc += f"`?{cmd.name} {cmd.signature}`\n"

        embed = discord.Embed(
            title=f"📂 {category}",
            description=desc or "No commands",
            color=discord.Color.blurple()
        )

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.add_item(HelpDropdown(bot))


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title="📖 Help Menu",
            description="Select a category below to view commands.",
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed, view=HelpView(self.bot))


async def setup(bot):
    await bot.add_cog(Help(bot))
