import discord
from discord.ext import commands
from discord.ui import Select, View
from datetime import datetime

class HelpView(View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx

    async def on_timeout(self):
        # Deaktiviere alle Children nach Timeout
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

class HelpSelect(Select):
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx
        
        # Optionen für das Dropdown-Menü
        options = []
        
        # Alle Cogs durchgehen
        for cog_name, cog in bot.cogs.items():
            commands_list = [cmd for cmd in cog.get_commands() if not cmd.hidden]
            if commands_list:
                # Emoji je nach Cog
                emoji = self.get_cog_emoji(cog_name)
                options.append(
                    discord.SelectOption(
                        label=cog_name,
                        description=f"{len(commands_list)} commands",
                        emoji=emoji,
                        value=cog_name
                    )
                )
        
        # Allgemeine Option
        options.append(
            discord.SelectOption(
                label="All Commands",
                description="Show all commands from all modules",
                emoji="📋",
                value="all"
            )
        )
        
        super().__init__(placeholder="📁 Select a module...", options=options, min_values=1, max_values=1)
    
    def get_cog_emoji(self, cog_name):
        emojis = {
            "Moderation": "🔨",
            "Utility": "🛠️",
            "Help": "❓",
            "Fun": "🎉",
            "Music": "🎵",
            "Economy": "💰",
            "Admin": "👑"
        }
        return emojis.get(cog_name, "📁")
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            embed = discord.Embed(
                description="❌ You cannot use this menu. Use `!help` yourself.",
                color=0xED4245,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        selected = self.values[0]
        
        if selected == "all":
            embed = self.create_all_commands_embed()
        else:
            cog = self.bot.get_cog(selected)
            if cog:
                embed = self.create_cog_embed(cog)
            else:
                embed = discord.Embed(
                    title="❌ Module not found",
                    description=f"`{selected}` module does not exist.",
                    color=0xED4245,
                    timestamp=datetime.utcnow()
                )
        
        await interaction.response.edit_message(embed=embed, view=self.view)
    
    def create_cog_embed(self, cog):
        """Erstellt ein Embed für einen bestimmten Cog"""
        commands_list = []
        for cmd in cog.get_commands():
            if not cmd.hidden:
                # Command Signatur bauen
                params = []
                for name, param in cmd.clean_params.items():
                    if param.default == param.empty:
                        params.append(f"<{name}>")
                    else:
                        params.append(f"[{name}]")
                
                signature = f"!{cmd.name} {' '.join(params)}" if params else f"!{cmd.name}"
                help_text = cmd.help or "No description"
                
                # Aliases
                alias_text = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
                
                commands_list.append(f"**{signature}**{alias_text}\n└─ *{help_text[:80]}*")
        
        embed = discord.Embed(
            title=f"{self.get_cog_emoji(cog.qualified_name)} {cog.qualified_name}",
            description=f"**{len(commands_list)} commands**",
            color=0x2b2d31,
            timestamp=datetime.utcnow()
        )
        
        # Teile die Commands in max 5 Fields auf
        chunk_size = max(1, (len(commands_list) + 4) // 5)
        for i in range(0, len(commands_list), chunk_size):
            chunk = commands_list[i:i+chunk_size]
            embed.add_field(
                name="‎",
                value="\n\n".join(chunk),
                inline=True
            )
        
        embed.set_footer(text="Use !help <command> for more details")
        return embed
    
    def create_all_commands_embed(self):
        """Erstellt ein Embed mit allen Commands gruppiert nach Cogs"""
        embed = discord.Embed(
            title="📋 All Commands",
            description="Here are all available modules and commands:",
            color=0x2b2d31,
            timestamp=datetime.utcnow()
        )
        
        total_commands = 0
        for cog_name, cog in self.bot.cogs.items():
            commands_list = [f"`!{cmd.name}`" for cmd in cog.get_commands() if not cmd.hidden]
            if commands_list:
                total_commands += len(commands_list)
                embed.add_field(
                    name=f"{self.get_cog_emoji(cog_name)} {cog_name}",
                    value=" ".join(commands_list[:15]) + ("..." if len(commands_list) > 15 else ""),
                    inline=False
                )
        
        embed.set_footer(text=f"Total: {total_commands} commands | Use the dropdown to see details")
        return embed

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx, *, command_name: str = None):
        """Show all commands with an interactive dropdown menu"""
        
        # Wenn ein bestimmter Command gesucht wird
        if command_name:
            cmd = self.bot.get_command(command_name.lower())
            if not cmd:
                embed = discord.Embed(
                    title="❌ Command not found",
                    description=f"`{command_name}` does not exist.\nUse `!help` to see all commands.",
                    color=0xED4245,
                    timestamp=datetime.utcnow()
                )
                await ctx.send(embed=embed)
                return
            
            # Command Details anzeigen
            params = []
            for name, param in cmd.clean_params.items():
                if param.default == param.empty:
                    params.append(f"<{name}>")
                else:
                    params.append(f"[{name}]")
            
            signature = f"!{cmd.name} {' '.join(params)}" if params else f"!{cmd.name}"
            
            embed = discord.Embed(
                title=f"📖 {cmd.name}",
                description=cmd.help or "No description available.",
                color=0x2b2d31,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Usage", value=f"`{signature}`", inline=False)
            
            if cmd.aliases:
                embed.add_field(name="Aliases", value=f"`{', '.join(cmd.aliases)}`", inline=False)
            
            embed.set_footer(text=f"Module: {cmd.cog.qualified_name if cmd.cog else 'Unknown'}")
            await ctx.send(embed=embed)
            return
        
        # Interaktives Help-Menü mit Dropdown
        view = HelpView(self.bot, ctx)
        select = HelpSelect(self.bot, ctx)
        view.add_item(select)
        
        # Initial Embed (erste Kategorie)
        first_cog = None
        for cog_name, cog in self.bot.cogs.items():
            if cog.get_commands():
                first_cog = cog
                break
        
        if first_cog:
            embed = select.create_cog_embed(first_cog)
        else:
            embed = discord.Embed(
                title="🤖 Bot Commands",
                description="No commands loaded.",
                color=0x2b2d31,
                timestamp=datetime.utcnow()
            )
        
        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Help(bot))
