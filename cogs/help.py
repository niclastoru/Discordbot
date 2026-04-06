import discord
from discord.ext import commands

class HelpDropdown(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        
        options = []
        for cog_name, cog in bot.cogs.items():
            if cog_name == "Help":
                continue
            commands_count = len(cog.get_commands())
            if commands_count > 0:
                options.append(
                    discord.SelectOption(
                        label=cog_name,
                        description=f"{commands_count} commands",
                        emoji=self.get_emoji(cog_name)
                    )
                )
        
        super().__init__(placeholder="📋 Select a category...", options=options)
    
    def get_emoji(self, name):
        emojis = {
            "Moderation": "🛡️",
            "Utility": "⚙️",
            "Admin": "👑",
            "Fun": "🎉",
            "Music": "🎵"
        }
        return emojis.get(name, "📁")
    
    async def callback(self, interaction: discord.Interaction):
        cog_name = self.values[0]
        cog = self.bot.get_cog(cog_name)
        
        commands_list = cog.get_commands()
        
        description = ""
        for cmd in commands_list:
            desc = cmd.help or "No description"
            description += f"`!{cmd.name}` - {desc}\n"
        
        embed = discord.Embed(
            title=f"{self.get_emoji(cog_name)} {cog_name} Commands",
            description=description or "No commands available.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"{len(commands_list)} commands • Use !help <command> for details")
        
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.add_item(HelpDropdown(bot))

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def help(self, ctx, command_name: str = None):
        """Shows help menu or details about a specific command"""
        
        if command_name:
            cmd = self.bot.get_command(command_name.lower())
            if cmd:
                embed = discord.Embed(
                    title=f"📖 Command: {cmd.name}",
                    description=cmd.help or "No description",
                    color=discord.Color.blue()
                )
                usage = f"`!{cmd.name}"
                if cmd.signature:
                    usage += f" {cmd.signature}"
                usage += "`"
                embed.add_field(name="Usage", value=usage, inline=False)
                if cmd.aliases:
                    embed.add_field(name="Aliases", value=", ".join([f"`!{a}`" for a in cmd.aliases]), inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Command `{command_name}` not found.")
            return
        
        total_commands = sum(len(cog.get_commands()) for cog in self.bot.cogs.values())
        
        embed = discord.Embed(
            title="📖 Bot Help Menu",
            description="Select a category from the dropdown menu below to see available commands.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Quick Tips", value="• `!help <command>` - Details about a command\n• `!cogs` - Show all loaded cogs", inline=False)
        embed.set_footer(text=f"Total: {total_commands} commands")
        
        await ctx.send(embed=embed, view=HelpView(self.bot))
    
    @commands.command()
    async def cogs(self, ctx):
        """Shows all loaded cogs and their command counts"""
        embed = discord.Embed(title="🔧 Loaded Cogs", color=discord.Color.green())
        for cog_name, cog in self.bot.cogs.items():
            cmd_count = len(cog.get_commands())
            embed.add_field(name=cog_name, value=f"{cmd_count} commands", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
