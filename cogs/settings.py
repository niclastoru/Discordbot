import discord
from discord.ext import commands

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("🔥🔥🔥 SETTINGS COG WURDE GELADEN! 🔥🔥🔥")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx):
        """Sets the jail role and jail channel"""
        embed = discord.Embed(title="✅ Jail Settings", description="This command works!", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Shows all current server settings"""
        embed = discord.Embed(title="⚙️ Server Settings", description="Settings command works!", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstaff(self, ctx):
        """Adds or removes staff roles"""
        embed = discord.Embed(title="👔 Staff Settings", description="Staff settings work!", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstafflist(self, ctx):
        """Lists all staff roles"""
        embed = discord.Embed(title="📋 Staff List", description="No staff roles set", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstaffwhitelist(self, ctx):
        """Adds or removes whitelist roles"""
        embed = discord.Embed(title="✅ Whitelist Settings", description="Whitelist works!", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def staff(self, ctx):
        """Staff management commands"""
        embed = discord.Embed(title="👔 Staff Management", description="Staff command works!", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings_jailmsg(self, ctx):
        """Sets the message sent when a user is jailed"""
        embed = discord.Embed(title="📝 Jail Message", description="Jail message command works!", color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    print("🔥🔥🔥 SETUP VON SETTINGS.PY WIRD AUSGEFÜHRT! 🔥🔥🔥")
    await bot.add_cog(Settings(bot))
    print("🔥🔥🔥 SETTINGS COG WURDE HINZUGEFÜGT! 🔥🔥🔥")
