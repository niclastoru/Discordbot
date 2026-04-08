import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Help Cog geladen")

    @commands.command()
    async def help(self, ctx, command_name: str = None):
        """Shows all commands or info about a specific command"""
        
        # Hilfe für einen bestimmten Befehl
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
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Command `{command_name}` not found.")
            return
        
        # Alle Commands aus allen Cogs sammeln
        categories = {}
        for cmd in self.bot.commands:
            if cmd.name == "help":
                continue
            cog_name = cmd.cog.__class__.__name__ if cmd.cog else "Other"
            if cog_name not in categories:
                categories[cog_name] = []
            categories[cog_name].append(f"`!{cmd.name}`")
        
        # Embed erstellen
        embed = discord.Embed(
            title="📖 Bot Commands",
            description="Use `!help <command>` for more details.",
            color=discord.Color.blue()
        )
        
        for cog_name, cmds in categories.items():
            embed.add_field(
                name=f"{cog_name} ({len(cmds)})",
                value="\n".join(cmds[:20]),
                inline=True
            )
        
        total = sum(len(cmds) for cmds in categories.values())
        embed.set_footer(text=f"Total: {total} commands")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
