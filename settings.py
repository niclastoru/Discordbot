import discord
from discord.ext import commands
from datetime import datetime
from database import db

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Settings Cog geladen")

    def create_embed(self, title, description, color, fields=None, footer=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        if footer:
            embed.set_footer(text=footer)
        return embed

    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, new_prefix: str = None):
        """Show or change the bot prefix"""
        if new_prefix is None:
            current = db.get_prefix(ctx.guild.id)
            embed = self.create_embed("📋 Current Prefix", f"Prefix: `{current}`", 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        db.set_prefix(ctx.guild.id, new_prefix)
        embed = self.create_embed("✅ Prefix Changed", f"New prefix: `{new_prefix}`", 0x57F287)
        await ctx.send(embed=embed)

    @commands.command(name="config")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        """Show all server settings"""
        prefix = db.get_prefix(ctx.guild.id)
        staff_roles = db.get_staff_roles(ctx.guild.id)
        
        staff_list = ", ".join([f"<@&{r}>" for r in staff_roles]) if staff_roles else "None"
        
        embed = self.create_embed(
            "⚙️ Server Settings",
            "",
            0x2b2d31,
            fields=[
                ("🔧 Prefix", prefix, True),
                ("👔 Staff Roles", staff_list, False),
                ("📊 Server ID", str(ctx.guild.id), True),
                ("👑 Owner", ctx.guild.owner.mention, True)
            ]
        )
        await ctx.send(embed=embed)

    # ========== STAFF ROLES ==========
    
    @commands.command(name="settingsstaff")
    @commands.has_permissions(administrator=True)
    async def settingsstaff(self, ctx, action: str, role: discord.Role = None):
        """Manage staff roles. Usage: !settingsstaff add @Mod or !settingsstaff remove @Mod or !settingsstaff list"""
        
        if action.lower() == "add":
            if role is None:
                embed = self.create_embed("❌ Missing Role", "Usage: `!settingsstaff add @role`", 0xED4245)
                await ctx.send(embed=embed)
                return
            
            db.add_staff_role(ctx.guild.id, role.id)
            embed = self.create_embed("✅ Staff Role Added", f"{role.mention} has been added as a staff role", 0x57F287)
            await ctx.send(embed=embed)
        
        elif action.lower() == "remove":
            if role is None:
                embed = self.create_embed("❌ Missing Role", "Usage: `!settingsstaff remove @role`", 0xED4245)
                await ctx.send(embed=embed)
                return
            
            if db.remove_staff_role(ctx.guild.id, role.id):
                embed = self.create_embed("✅ Staff Role Removed", f"{role.mention} has been removed from staff roles", 0x57F287)
            else:
                embed = self.create_embed("❌ Not Found", f"{role.mention} is not a staff role", 0xED4245)
            await ctx.send(embed=embed)
        
        elif action.lower() == "list":
            staff_roles = db.get_staff_roles(ctx.guild.id)
            
            if not staff_roles:
                embed = self.create_embed("📋 Staff Roles", "No staff roles configured.\nUse `!settingsstaff add @role` to add one.", 0xFEE75C)
            else:
                roles_list = "\n".join([f"• <@&{r}>" for r in staff_roles])
                embed = self.create_embed("📋 Staff Roles", roles_list, 0x2b2d31, footer=f"Total: {len(staff_roles)} staff roles")
            await ctx.send(embed=embed)
        
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add`, `remove`, or `list`", 0xED4245)
            await ctx.send(embed=embed)

    # ========== STAFF COMMAND (zeigt online staff) ==========
    
    @commands.command(name="staff")
    async def staff(self, ctx):
        """Show all online staff members"""
        staff_role_ids = db.get_staff_roles(ctx.guild.id)
        
        if not staff_role_ids:
            embed = self.create_embed("👔 Staff Members", "No staff roles configured.\nUse `!settingsstaff add @role` to add staff roles.", 0xFEE75C)
            await ctx.send(embed=embed)
            return
        
        # Collect all members with staff roles
        staff_members = []
        for role_id in staff_role_ids:
            role = ctx.guild.get_role(int(role_id))
            if role:
                for member in role.members:
                    if member not in staff_members and not member.bot:
                        staff_members.append(member)
        
        if not staff_members:
            embed = self.create_embed("👔 Staff Members", "No staff members found.", 0xFEE75C)
            await ctx.send(embed=embed)
            return
        
        # Separate online and offline
        online = []
        offline = []
        
        for member in staff_members:
            if member.status != discord.Status.offline:
                status_emoji = "🟢" if member.status == discord.Status.online else "🌙" if member.status == discord.Status.idle else "🔴"
                online.append(f"{status_emoji} {member.mention}")
            else:
                offline.append(f"⚫ {member.mention}")
        
        embed = self.create_embed(
            "👔 Staff Members",
            "",
            0x2b2d31,
            footer=f"Total: {len(staff_members)} staff members"
        )
        
        if online:
            embed.add_field(name="🟢 Online", value="\n".join(online[:20]), inline=False)
        if offline:
            embed.add_field(name="⚫ Offline", value="\n".join(offline[:10]) if offline else "None", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))
