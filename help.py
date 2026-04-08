import discord
from discord.ext import commands
from discord.ui import Select, View
from datetime import datetime

class HelpView(View):
    def __init__(self, bot, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.ctx = ctx
        self.message = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass

class HelpSelect(Select):
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx
        
        options = []
        
        for cog_name, cog in bot.cogs.items():
            cmd_count = len([cmd for cmd in cog.get_commands() if not cmd.hidden])
            if cmd_count > 0 and cog_name.lower() != "help":
                emoji = "🔨" if "mod" in cog_name.lower() else "🛠️" if "util" in cog_name.lower() else "⚙️" if "admin" in cog_name.lower() else "📁"
                options.append(
                    discord.SelectOption(
                        label=cog_name,
                        description=f"{cmd_count} commands",
                        emoji=emoji,
                        value=cog_name
                    )
                )
        
        if options:
            options.append(
                discord.SelectOption(
                    label="All Commands",
                    description="Show all commands from all modules",
                    emoji="📋",
                    value="all"
                )
            )
        
        if not options:
            options.append(discord.SelectOption(label="No modules loaded", value="none"))
        
        super().__init__(placeholder="📁 Select a module...", options=options, min_values=1, max_values=1)
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            embed = discord.Embed(description="❌ This menu is not for you. Use `!help` yourself.", color=0xED4245)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        selected = self.values[0]
        
        if selected == "all":
            embed = self.create_all_embed()
        elif selected == "none":
            embed = discord.Embed(title="❌ No modules", description="No commands loaded yet.", color=0xFEE75C)
        else:
            cog = self.bot.get_cog(selected)
            if cog:
                embed = self.create_cog_embed(cog)
            else:
                embed = discord.Embed(title="❌ Module not found", color=0xED4245)
        
        await interaction.response.edit_message(embed=embed, view=self.view)
    
    def create_cog_embed(self, cog):
        commands_list = []
        for cmd in cog.get_commands():
            if not cmd.hidden:
                params = []
                for name, param in cmd.clean_params.items():
                    if param.default == param.empty:
                        params.append(f"<{name}>")
                    else:
                        params.append(f"[{name}]")
                
                signature = f"!{cmd.name} {' '.join(params)}" if params else f"!{cmd.name}"
                help_text = (cmd.help or "No description")[:80]
                alias_text = f" (alias: {', '.join(cmd.aliases)})" if cmd.aliases else ""
                commands_list.append(f"**`{signature}`**{alias_text}\n*{help_text}*")
        
        embed = discord.Embed(
            title=f"📁 {cog.qualified_name}",
            description=f"**{len(commands_list)} commands**",
            color=0x2b2d31,
            timestamp=datetime.utcnow()
        )
        
        if commands_list:
            chunk_size = max(1, (len(commands_list) + 4) // 5)
            for i in range(0, len(commands_list), chunk_size):
                chunk = commands_list[i:i+chunk_size]
                embed.add_field(name="‎", value="\n\n".join(chunk), inline=True)
        
        embed.set_footer(text="Use !help <command> for details")
        return embed
    
    def create_all_embed(self):
        embed = discord.Embed(
            title="📋 All Commands",
            description="Select a module from the dropdown for details.",
            color=0x2b2d31,
            timestamp=datetime.utcnow()
        )
        
        total = 0
        for cog_name, cog in self.bot.cogs.items():
            if cog_name.lower() == "help":
                continue
            cmds = [f"`!{cmd.name}`" for cmd in cog.get_commands() if not cmd.hidden]
            if cmds:
                total += len(cmds)
                embed.add_field(
                    name=f"📁 {cog_name}",
                    value=" ".join(cmds[:15]) + ("..." if len(cmds) > 15 else ""),
                    inline=False
                )
        
        embed.set_footer(text=f"Total: {total} commands")
        return embed

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Help Cog geladen")

    @commands.command(name="help")
    async def help_command(self, ctx, *, command_name: str = None):
        if command_name:
            cmd = self.bot.get_command(command_name.lower())
            if not cmd:
                embed = discord.Embed(title="❌ Command not found", description=f"`{command_name}` doesn't exist.", color=0xED4245)
                await ctx.send(embed=embed)
                return
            
            params = []
            for name, param in cmd.clean_params.items():
                if param.default == param.empty:
                    params.append(f"<{name}>")
                else:
                    params.append(f"[{name}]")
            
            signature = f"!{cmd.name} {' '.join(params)}" if params else f"!{cmd.name}"
            
            embed = discord.Embed(title=f"📖 {cmd.name}", description=cmd.help or "No description", color=0x2b2d31)
            embed.add_field(name="Usage", value=f"`{signature}`", inline=False)
            if cmd.aliases:
                embed.add_field(name="Aliases", value=f"`{', '.join(cmd.aliases)}`", inline=False)
            embed.set_footer(text=f"Module: {cmd.cog.qualified_name if cmd.cog else 'Unknown'}")
            await ctx.send(embed=embed)
            return
        
        view = HelpView(self.bot, ctx)
        select = HelpSelect(self.bot, ctx)
        view.add_item(select)
        
        first_cog = None
        for cog_name, cog in self.bot.cogs.items():
            if cog_name.lower() != "help" and len(cog.get_commands()) > 0:
                first_cog = cog
                break
        
        if first_cog:
            embed = select.create_cog_embed(first_cog)
        else:
            embed = select.create_all_embed()
        
        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Help(bot))
