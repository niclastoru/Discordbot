import discord
from discord.ext import commands
from discord.ui import Select, View

class HelpView(View):
    def __init__(self, bot, ctx, categories):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.categories = categories

        # Dropdown automatisch aus den gefundenen Kategorien befüllen
        options = []
        for cog_name, commands_list in categories.items():
            if commands_list:  # Nur Kategorien mit Commands anzeigen
                options.append(
                    discord.SelectOption(
                        label=f"{self.get_emoji_for_cog(cog_name)} {cog_name}",
                        description=f"{len(commands_list)} commands",
                        value=cog_name
                    )
                )
        
        # Wenn es Optionen gibt, Dropdown erstellen
        if options:
            self.select = discord.ui.Select(
                placeholder="Select a category...",
                options=options[:25]  # Max 25 Optionen pro Dropdown
            )
            self.select.callback = self.select_callback
            self.add_item(self.select)

    def get_emoji_for_cog(self, cog_name):
        """Gibt passendes Emoji für jede Cog-Kategorie zurück"""
        emojis = {
            "Moderation": "🛡️",
            "Utility": "⚙️",
            "Admin": "👑",
            "Help": "❓",
            "Ticket": "🎫",
            "Music": "🎵",
            "Economy": "💰",
            "Fun": "🎉"
        }
        return emojis.get(cog_name, "📁")

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ This menu is not for you!", ephemeral=True)
            return
        
        cog_name = interaction.data["values"][0]
        embed = self.get_category_embed(cog_name)
        await interaction.response.edit_message(embed=embed, view=self)

    def get_category_embed(self, cog_name):
        """Erstellt Embed für eine Kategorie"""
        commands_list = self.categories.get(cog_name, [])
        
        embed = discord.Embed(
            title=f"{self.get_emoji_for_cog(cog_name)} {cog_name} Commands",
            description=f"**{len(commands_list)} commands available**\nUse `!help <command>` for more details.",
            color=discord.Color.blue()
        )
        
        if commands_list:
            # Sortieren und in zwei Spalten aufteilen
            commands_list = sorted(commands_list)
            half = len(commands_list) // 2
            
            embed.add_field(
                name="Commands",
                value="\n".join([f"`!{cmd}`" for cmd in commands_list[:half]]) if commands_list[:half] else "None",
                inline=True
            )
            embed.add_field(
                name="Continued",
                value="\n".join([f"`!{cmd}`" for cmd in commands_list[half:]]) if commands_list[half:] else "None",
                inline=True
            )
        
        embed.set_footer(text=f"Total: {len(commands_list)} commands")
        return embed


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_all_commands_by_cog(self):
        """Sammelt automatisch alle Commands aus allen Cogs"""
        categories = {}
        
        for cmd in self.bot.commands:
            if cmd.name == "help":
                continue  # Help Command selbst überspringen
            
            # Cog Namen bestimmen
            if cmd.cog:
                cog_name = cmd.cog.__class__.__name__
            else:
                cog_name = "Other"
            
            # Command zur Kategorie hinzufügen
            if cog_name not in categories:
                categories[cog_name] = []
            
            if cmd.name not in categories[cog_name]:
                categories[cog_name].append(cmd.name)
        
        return categories

    @commands.command()
    async def help(self, ctx, command_name: str = None):
        """Shows the help menu or details about a specific command"""
        
        # Wenn ein bestimmter Command abgefragt wird
        if command_name:
            cmd = self.bot.get_command(command_name.lower())
            if cmd:
                embed = discord.Embed(
                    title=f"📖 Command: {cmd.name}",
                    description=cmd.help or "No description available.",
                    color=discord.Color.blue()
                )
                
                # Usage
                usage = f"`!{cmd.name}"
                if cmd.signature:
                    usage += f" {cmd.signature}"
                usage += "`"
                embed.add_field(name="Usage", value=usage, inline=False)
                
                # Aliases
                if cmd.aliases:
                    embed.add_field(name="Aliases", value=", ".join([f"`!{a}`" for a in cmd.aliases]), inline=False)
                
                # Category
                if cmd.cog:
                    embed.add_field(name="Category", value=cmd.cog.__class__.__name__, inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Command `{command_name}` not found. Use `!help` to see all commands.")
            return
        
        # Hauptmenu - automatisch alle Kategorien erkennen
        categories = self.get_all_commands_by_cog()
        
        # Gesamtanzahl der Commands
        total_commands = sum(len(cmds) for cmds in categories.values())
        
        embed = discord.Embed(
            title="📖 Bot Help Menu",
            description=f"Welcome to the bot! Select a category from the dropdown menu below to see available commands.\n\n**Quick Tips:**\n• Use `!help <command>` for detailed info\n• Total commands: **{total_commands}**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        view = HelpView(self.bot, ctx, categories)
        
        # Wenn keine Kategorien existieren, einfachen Embed senden
        if not view.children:
            embed.add_field(name="No Commands Found", value="Make sure cogs are loaded correctly.", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed, view=view)

    @commands.command()
    async def commands(self, ctx, category: str = None):
        """Shows all commands in a specific category: !commands Moderation"""
        
        categories = self.get_all_commands_by_cog()
        
        if not category:
            # Zeige alle Kategorien an
            cat_list = "\n".join([f"• {name} ({len(cmds)} commands)" for name, cmds in categories.items()])
            embed = discord.Embed(
                title="📋 Available Categories",
                description=f"{cat_list}\n\nUse `!commands <category>` to see commands in a category.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Bestimmte Kategorie suchen (case-insensitive)
        found_cog = None
        for cog_name in categories.keys():
            if cog_name.lower() == category.lower():
                found_cog = cog_name
                break
        
        if found_cog:
            commands_list = sorted(categories[found_cog])
            embed = discord.Embed(
                title=f"📋 {found_cog} Commands",
                description="\n".join([f"`!{cmd}`" for cmd in commands_list]),
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Category `{category}` not found. Available: {', '.join(categories.keys())}")

    @commands.command()
    async def cogs(self, ctx):
        """Shows all loaded cogs and their command counts"""
        categories = self.get_all_commands_by_cog()
        
        embed = discord.Embed(
            title="🔧 Loaded Cogs",
            description=f"**Total Cogs:** {len(categories)}\n**Total Commands:** {sum(len(cmds) for cmds in categories.values())}",
            color=discord.Color.green()
        )
        
        for cog_name, commands_list in categories.items():
            embed.add_field(
                name=cog_name,
                value=f"{len(commands_list)} commands",
                inline=True
            )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
