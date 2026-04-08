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

    async def is_admin(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            embed = self.create_embed("⛔ Permission Denied", "You need `Administrator` permission.", 0xED4245)
            await ctx.send(embed=embed)
            return False
        return True

    # ========== 1. JAIL-SETTINGS ==========
    @commands.command(name="jail-settings")
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx, role: discord.Role = None):
        """Set or view the jail role"""
        if role:
            db.set_jail_role(ctx.guild.id, role.id)
            embed = self.create_embed("⚙️ Jail Role Set", f"Jail role: {role.mention}", 0x57F287)
        else:
            role_id = db.get_jail_role(ctx.guild.id)
            r = ctx.guild.get_role(int(role_id)) if role_id else None
            embed = self.create_embed("⚙️ Current Jail Role", r.mention if r else "Not set", 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 2. SETTINGS-JAILMSG ==========
    @commands.command(name="settings-jailmsg")
    @commands.has_permissions(administrator=True)
    async def settings_jailmsg(self, ctx, *, message: str = None):
        """Set custom jail message for users"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        
        if message:
            current["jail_message"] = message
            db.update_guild_settings(ctx.guild.id, "settings", current)
            embed = self.create_embed("✅ Jail Message Set", f"New message:\n{message[:500]}", 0x57F287)
        else:
            msg = current.get("jail_message", "You have been jailed for violating server rules.")
            embed = self.create_embed("📝 Current Jail Message", msg[:1000], 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 3. SETTINGS ==========
    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """View all server settings"""
        settings = db.get_guild_settings(ctx.guild.id)
        s = settings.get("settings", {})
        
        # Get staff roles
        staff_roles = s.get("staff_roles", [])
        staff_list = ", ".join([f"<@&{r}>" for r in staff_roles]) if staff_roles else "None"
        
        embed = self.create_embed(
            "⚙️ Server Settings Overview",
            "",
            0x2b2d31,
            fields=[
                ("🔧 Jail Role", f"<@&{db.get_jail_role(ctx.guild.id)}>" if db.get_jail_role(ctx.guild.id) else "Not set", True),
                ("📝 Jail Message", "Set" if s.get("jail_message") else "Default", True),
                ("👔 Staff Roles", staff_list[:100], False),
                ("👑 Staff Whitelist", str(len(s.get("staff_whitelist", []))), True),
                ("🛡️ Anti-Nuke", "Enabled" if s.get("antinuke") else "Disabled", True),
                ("🛡️ Anti-Raid", "Enabled" if s.get("antiraid") else "Disabled", True),
                ("📜 Rules", "Set" if s.get("rules") else "Not set", True)
            ]
        )
        await ctx.send(embed=embed)

    # ========== 4. SETTINGSSTAFF ==========
    @commands.command(name="settingsstaff")
    @commands.has_permissions(administrator=True)
    async def settings_staff(self, ctx, action: str, role: discord.Role = None):
        """Manage staff roles. Usage: !settingsstaff add @Mod or !settingsstaff remove @Mod"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        staff_roles = current.get("staff_roles", [])
        
        if action.lower() == "add":
            if not role:
                embed = self.create_embed("❌ Missing Role", "Usage: `!settingsstaff add @role`", 0xED4245)
            elif str(role.id) in staff_roles:
                embed = self.create_embed("⚠️ Already Staff", f"{role.mention} is already a staff role", 0xFEE75C)
            else:
                staff_roles.append(str(role.id))
                current["staff_roles"] = staff_roles
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Staff Role Added", f"{role.mention} has been added as staff role", 0x57F287)
        
        elif action.lower() == "remove":
            if not role:
                embed = self.create_embed("❌ Missing Role", "Usage: `!settingsstaff remove @role`", 0xED4245)
            elif str(role.id) not in staff_roles:
                embed = self.create_embed("⚠️ Not Staff", f"{role.mention} is not a staff role", 0xFEE75C)
            else:
                staff_roles.remove(str(role.id))
                current["staff_roles"] = staff_roles
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Staff Role Removed", f"{role.mention} has been removed from staff roles", 0x57F287)
        
        elif action.lower() == "list":
            if not staff_roles:
                embed = self.create_embed("📋 Staff Roles", "No staff roles configured.", 0xFEE75C)
            else:
                roles_list = "\n".join([f"• <@&{r}>" for r in staff_roles])
                embed = self.create_embed("📋 Staff Roles", roles_list, 0x2b2d31, footer=f"Total: {len(staff_roles)}")
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add`, `remove`, or `list`", 0xED4245)
        
        await ctx.send(embed=embed)

    # ========== 5. SETTINGSSTAFFLIST ==========
    @commands.command(name="settingsstafflist")
    @commands.has_permissions(administrator=True)
    async def settings_staff_list(self, ctx):
        """List all staff roles"""
        settings = db.get_guild_settings(ctx.guild.id)
        staff_roles = settings.get("settings", {}).get("staff_roles", [])
        
        if not staff_roles:
            embed = self.create_embed("📋 Staff Role List", "No staff roles configured.\nUse `!settingsstaff add @role` to add one.", 0xFEE75C)
        else:
            roles_list = "\n".join([f"• <@&{r}>" for r in staff_roles])
            embed = self.create_embed("📋 Staff Role List", roles_list, 0x2b2d31, footer=f"Total: {len(staff_roles)} staff roles")
        await ctx.send(embed=embed)

    # ========== 6. SETTINGSSTAFFWHITELIST ==========
    @commands.command(name="settingsstaffwhitelist")
    @commands.has_permissions(administrator=True)
    async def settings_staff_whitelist(self, ctx, action: str, user: discord.Member = None):
        """Manage staff whitelist (users who can use staff commands)"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        whitelist = current.get("staff_whitelist", [])
        
        if action.lower() == "add":
            if not user:
                embed = self.create_embed("❌ Missing User", "Usage: `!settingsstaffwhitelist add @user`", 0xED4245)
            elif str(user.id) in whitelist:
                embed = self.create_embed("⚠️ Already Whitelisted", f"{user.mention} is already whitelisted", 0xFEE75C)
            else:
                whitelist.append(str(user.id))
                current["staff_whitelist"] = whitelist
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ User Whitelisted", f"{user.mention} can now use staff commands", 0x57F287)
        
        elif action.lower() == "remove":
            if not user:
                embed = self.create_embed("❌ Missing User", "Usage: `!settingsstaffwhitelist remove @user`", 0xED4245)
            elif str(user.id) not in whitelist:
                embed = self.create_embed("⚠️ Not Whitelisted", f"{user.mention} is not whitelisted", 0xFEE75C)
            else:
                whitelist.remove(str(user.id))
                current["staff_whitelist"] = whitelist
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ User Removed", f"{user.mention} removed from whitelist", 0x57F287)
        
        elif action.lower() == "list":
            if not whitelist:
                embed = self.create_embed("📋 Staff Whitelist", "No users whitelisted.", 0xFEE75C)
            else:
                users_list = "\n".join([f"• <@{u}>" for u in whitelist])
                embed = self.create_embed("📋 Staff Whitelist", users_list, 0x2b2d31, footer=f"Total: {len(whitelist)} users")
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add`, `remove`, or `list`", 0xED4245)
        
        await ctx.send(embed=embed)

    # ========== 7. STAFF ==========
    @commands.command(name="staff")
    @commands.has_permissions(kick_members=True)
    async def staff(self, ctx):
        """Show all online staff members"""
        settings = db.get_guild_settings(ctx.guild.id)
        staff_roles = settings.get("settings", {}).get("staff_roles", [])
        whitelist = settings.get("settings", {}).get("staff_whitelist", [])
        
        # Collect all staff members
        staff_members = []
        
        # Members with staff roles
        for role_id in staff_roles:
            role = ctx.guild.get_role(int(role_id))
            if role:
                for member in role.members:
                    if member not in staff_members and not member.bot:
                        staff_members.append(member)
        
        # Whitelisted users
        for user_id in whitelist:
            member = ctx.guild.get_member(int(user_id))
            if member and member not in staff_members and not member.bot:
                staff_members.append(member)
        
        if not staff_members:
            embed = self.create_embed("👔 Staff Members", "No staff members configured.\nUse `!settingsstaff add @role` to add staff roles.", 0xFEE75C)
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

    # ========== HELPER: Check if user is staff ==========
    async def is_staff(self, ctx, user: discord.Member = None):
        """Check if a user is staff (has staff role or is whitelisted)"""
        user = user or ctx.author
        
        settings = db.get_guild_settings(ctx.guild.id)
        staff_roles = settings.get("settings", {}).get("staff_roles", [])
        whitelist = settings.get("settings", {}).get("staff_whitelist", [])
        
        # Check staff roles
        for role_id in staff_roles:
            role = ctx.guild.get_role(int(role_id))
            if role and role in user.roles:
                return True
        
        # Check whitelist
        if str(user.id) in whitelist:
            return True
        
        # Check admin permission
        if user.guild_permissions.administrator:
            return True
        
        return False

    # ========== JAIL LISTENER WITH CUSTOM MESSAGE ==========
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Send custom jail message when user gets jailed"""
        if before.roles == after.roles:
            return
        
        settings = db.get_guild_settings(after.guild.id)
        jail_role_id = db.get_jail_role(after.guild.id)
        
        if not jail_role_id:
            return
        
        jail_role = after.guild.get_role(int(jail_role_id))
        
        # User was jailed (got the jail role)
        if jail_role and jail_role not in before.roles and jail_role in after.roles:
            jail_msg = settings.get("settings", {}).get("jail_message", "You have been jailed for violating server rules.")
            
            try:
                embed = self.create_embed("⛓️ You have been jailed", jail_msg, 0xED4245)
                await after.send(embed=embed)
            except:
                pass

async def setup(bot):
    await bot.add_cog(Settings(bot))
