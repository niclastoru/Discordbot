import discord
from discord.ext import commands
from datetime import datetime
import sqlite3
import asyncio

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "settings.db"
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Main settings table
        c.execute('''CREATE TABLE IF NOT EXISTS server_settings (
            guild_id TEXT PRIMARY KEY,
            jail_role TEXT,
            jail_channel TEXT,
            jail_message TEXT,
            log_channel TEXT,
            staff_roles TEXT,
            whitelist_roles TEXT
        )''')
        
        # Staff roles list (separate table for multiple roles)
        c.execute('''CREATE TABLE IF NOT EXISTS staff_roles (
            guild_id TEXT,
            role_id TEXT,
            PRIMARY KEY (guild_id, role_id)
        )''')
        
        # Whitelist roles list
        c.execute('''CREATE TABLE IF NOT EXISTS whitelist_roles (
            guild_id TEXT,
            role_id TEXT,
            PRIMARY KEY (guild_id, role_id)
        )''')
        
        conn.commit()
        conn.close()

    # ========== HELPER METHODS ==========
    def get_setting(self, guild_id, key):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(f"SELECT {key} FROM server_settings WHERE guild_id = ?", (str(guild_id),))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def set_setting(self, guild_id, key, value):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(f"INSERT OR REPLACE INTO server_settings (guild_id, {key}) VALUES (?, ?)", (str(guild_id), value))
        conn.commit()
        conn.close()

    def get_staff_roles(self, guild_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_id FROM staff_roles WHERE guild_id = ?", (str(guild_id),))
        result = [row[0] for row in c.fetchall()]
        conn.close()
        return result

    def add_staff_role(self, guild_id, role_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO staff_roles (guild_id, role_id) VALUES (?, ?)", (str(guild_id), str(role_id)))
        conn.commit()
        conn.close()

    def remove_staff_role(self, guild_id, role_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM staff_roles WHERE guild_id = ? AND role_id = ?", (str(guild_id), str(role_id)))
        conn.commit()
        conn.close()

    def get_whitelist_roles(self, guild_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_id FROM whitelist_roles WHERE guild_id = ?", (str(guild_id),))
        result = [row[0] for row in c.fetchall()]
        conn.close()
        return result

    def add_whitelist_role(self, guild_id, role_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO whitelist_roles (guild_id, role_id) VALUES (?, ?)", (str(guild_id), str(role_id)))
        conn.commit()
        conn.close()

    def remove_whitelist_role(self, guild_id, role_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM whitelist_roles WHERE guild_id = ? AND role_id = ?", (str(guild_id), str(role_id)))
        conn.commit()
        conn.close()

    async def error_embed(self, ctx, title, description, example=None):
        embed = discord.Embed(title=f"❌ {title}", description=description, color=discord.Color.red())
        if example:
            embed.add_field(name="📝 Example", value=f"`{example}`", inline=False)
        await ctx.send(embed=embed)

    async def success_embed(self, ctx, title, description, color=discord.Color.green()):
        embed = discord.Embed(title=f"✅ {title}", description=description, color=color)
        await ctx.send(embed=embed)

    # ========== JAIL-SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx, role: discord.Role = None, channel: discord.TextChannel = None):
        """Sets the jail role and jail channel. Usage: !jail_settings @Jailed #jail-channel"""
        if role is None and channel is None:
            # Show current settings
            current_role_id = self.get_setting(ctx.guild.id, "jail_role")
            current_channel_id = self.get_setting(ctx.guild.id, "jail_channel")
            
            embed = discord.Embed(title="⚙️ Current Jail Settings", color=discord.Color.blue())
            
            if current_role_id:
                role_obj = ctx.guild.get_role(int(current_role_id))
                embed.add_field(name="Jail Role", value=role_obj.mention if role_obj else f"`{current_role_id}` (deleted)", inline=True)
            else:
                embed.add_field(name="Jail Role", value="Not set", inline=True)
            
            if current_channel_id:
                channel_obj = ctx.guild.get_channel(int(current_channel_id))
                embed.add_field(name="Jail Channel", value=channel_obj.mention if channel_obj else f"`{current_channel_id}` (deleted)", inline=True)
            else:
                embed.add_field(name="Jail Channel", value="Not set", inline=True)
            
            await ctx.send(embed=embed)
            return
        
        if role:
            self.set_setting(ctx.guild.id, "jail_role", str(role.id))
        if channel:
            self.set_setting(ctx.guild.id, "jail_channel", str(channel.id))
        
        await self.success_embed(ctx, "Jail Settings Updated", 
                                  f"**Role:** {role.mention if role else 'unchanged'}\n**Channel:** {channel.mention if channel else 'unchanged'}", 
                                  discord.Color.green())

    # ========== SETTINGS-JAILMSG ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings_jailmsg(self, ctx, *, message: str = None):
        """Sets the message sent when a user is jailed. Use {user} for mention, {reason} for reason."""
        if message is None:
            current = self.get_setting(ctx.guild.id, "jail_message")
            embed = discord.Embed(title="📝 Current Jail Message", color=discord.Color.blue())
            if current:
                embed.description = current
                embed.add_field(name="Variables", value="`{user}` - Mentions the jailed user\n`{reason}` - Shows the reason", inline=False)
            else:
                embed.description = "No custom jail message set.\nDefault: `{user} has been jailed. Reason: {reason}`"
                embed.add_field(name="Example", value="`!settings_jailmsg {user} was jailed for {reason}`", inline=False)
            await ctx.send(embed=embed)
            return
        
        self.set_setting(ctx.guild.id, "jail_message", message)
        await self.success_embed(ctx, "Jail Message Updated", 
                                  f"New message:\n```{message}```\nUse `{{user}}` for user mention, `{{reason}}` for reason.", 
                                  discord.Color.green())

    # ========== SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Shows all current server settings"""
        jail_role_id = self.get_setting(ctx.guild.id, "jail_role")
        jail_channel_id = self.get_setting(ctx.guild.id, "jail_channel")
        jail_msg = self.get_setting(ctx.guild.id, "jail_message")
        log_channel_id = self.get_setting(ctx.guild.id, "log_channel")
        
        staff_roles = self.get_staff_roles(ctx.guild.id)
        whitelist_roles = self.get_whitelist_roles(ctx.guild.id)
        
        embed = discord.Embed(title=f"⚙️ Server Settings - {ctx.guild.name}", color=discord.Color.blue(), timestamp=datetime.now())
        
        # Jail Settings
        jail_role = ctx.guild.get_role(int(jail_role_id)) if jail_role_id else None
        jail_channel = ctx.guild.get_channel(int(jail_channel_id)) if jail_channel_id else None
        embed.add_field(name="🔒 Jail Role", value=jail_role.mention if jail_role else "Not set", inline=True)
        embed.add_field(name="🔒 Jail Channel", value=jail_channel.mention if jail_channel else "Not set", inline=True)
        embed.add_field(name="📝 Jail Message", value="Custom" if jail_msg else "Default", inline=True)
        
        # Staff Roles
        if staff_roles:
            roles_list = []
            for role_id in staff_roles[:5]:
                role = ctx.guild.get_role(int(role_id))
                if role:
                    roles_list.append(role.mention)
            embed.add_field(name="👔 Staff Roles", value="\n".join(roles_list) if roles_list else "None", inline=False)
        else:
            embed.add_field(name="👔 Staff Roles", value="No staff roles set", inline=False)
        
        # Whitelist Roles
        if whitelist_roles:
            roles_list = []
            for role_id in whitelist_roles[:5]:
                role = ctx.guild.get_role(int(role_id))
                if role:
                    roles_list.append(role.mention)
            embed.add_field(name="✅ Whitelist Roles", value="\n".join(roles_list) if roles_list else "None", inline=False)
        else:
            embed.add_field(name="✅ Whitelist Roles", value="No whitelist roles set", inline=False)
        
        embed.set_footer(text="Use individual commands to modify these settings")
        await ctx.send(embed=embed)

    # ========== SETTINGSSTAFF ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstaff(self, ctx, action: str = None, role: discord.Role = None):
        """Adds or removes staff roles. Usage: !settingsstaff add @role | !settingsstaff remove @role"""
        if action is None or role is None:
            await self.error_embed(ctx, "Missing Arguments", "You need to specify an action and a role.", 
                                    "settingsstaff add @Moderator\nsettingsstaff remove @Moderator")
            return
        
        if action.lower() == "add":
            self.add_staff_role(ctx.guild.id, role.id)
            await self.success_embed(ctx, "Staff Role Added", f"{role.mention} has been added to staff roles.", discord.Color.green())
        
        elif action.lower() == "remove":
            self.remove_staff_role(ctx.guild.id, role.id)
            await self.success_embed(ctx, "Staff Role Removed", f"{role.mention} has been removed from staff roles.", discord.Color.red())
        
        else:
            await self.error_embed(ctx, "Invalid Action", "Use `add` or `remove`.", "settingsstaff add @Moderator")

    # ========== SETTINGSSTAFFLIST ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstafflist(self, ctx):
        """Lists all staff roles"""
        staff_roles = self.get_staff_roles(ctx.guild.id)
        
        if not staff_roles:
            await self.error_embed(ctx, "No Staff Roles", "No staff roles have been set up.\nUse `!settingsstaff add @role` to add one.", None)
            return
        
        roles_list = []
        for role_id in staff_roles:
            role = ctx.guild.get_role(int(role_id))
            if role:
                roles_list.append(f"• {role.mention} (ID: {role.id})")
            else:
                roles_list.append(f"• Deleted role (ID: {role_id})")
        
        embed = discord.Embed(title=f"👔 Staff Roles ({len(roles_list)})", description="\n".join(roles_list), color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== SETTINGSSTAFFWHITELIST ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstaffwhitelist(self, ctx, action: str = None, role: discord.Role = None):
        """Adds or removes whitelist roles. Usage: !settingsstaffwhitelist add @role | !settingsstaffwhitelist remove @role"""
        if action is None or role is None:
            await self.error_embed(ctx, "Missing Arguments", "You need to specify an action and a role.", 
                                    "settingsstaffwhitelist add @Trusted\nsettingsstaffwhitelist remove @Trusted")
            return
        
        if action.lower() == "add":
            self.add_whitelist_role(ctx.guild.id, role.id)
            await self.success_embed(ctx, "Whitelist Role Added", f"{role.mention} has been added to whitelist.", discord.Color.green())
        
        elif action.lower() == "remove":
            self.remove_whitelist_role(ctx.guild.id, role.id)
            await self.success_embed(ctx, "Whitelist Role Removed", f"{role.mention} has been removed from whitelist.", discord.Color.red())
        
        else:
            await self.error_embed(ctx, "Invalid Action", "Use `add` or `remove`.", "settingsstaffwhitelist add @Trusted")

    # ========== STAFF ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def staff(self, ctx, action: str = None, member: discord.Member = None, *, reason: str = None):
        """Staff management commands. Usage: !staff add @user | !staff remove @user | !staff list"""
        
        if action is None:
            embed = discord.Embed(title="👔 Staff Commands", color=discord.Color.blue())
            embed.add_field(name="Add Staff", value="`!staff add @user` - Adds staff role to a member", inline=False)
            embed.add_field(name="Remove Staff", value="`!staff remove @user` - Removes staff role from a member", inline=False)
            embed.add_field(name="List Staff", value="`!staff list` - Lists all staff members", inline=False)
            await ctx.send(embed=embed)
            return
        
        staff_roles_ids = self.get_staff_roles(ctx.guild.id)
        if not staff_roles_ids:
            await self.error_embed(ctx, "No Staff Roles Configured", "Please set up staff roles first using `!settingsstaff add @role`", None)
            return
        
        staff_roles = [ctx.guild.get_role(int(rid)) for rid in staff_roles_ids if ctx.guild.get_role(int(rid))]
        staff_roles = [r for r in staff_roles if r is not None]
        
        if not staff_roles:
            await self.error_embed(ctx, "No Valid Staff Roles", "The configured staff roles no longer exist.", "settingsstaff add @Moderator")
            return
        
        # List staff members
        if action.lower() == "list":
            staff_members = []
            for member in ctx.guild.members:
                for role in staff_roles:
                    if role in member.roles:
                        staff_members.append(f"• {member.mention} - {member.name}")
                        break
            
            if not staff_members:
                await self.error_embed(ctx, "No Staff Members", "No members have staff roles.", None)
            else:
                embed = discord.Embed(title=f"👔 Staff Members ({len(staff_members)})", description="\n".join(staff_members), color=discord.Color.blue())
                await ctx.send(embed=embed)
            return
        
        # Add staff role to member
        if action.lower() == "add":
            if member is None:
                await self.error_embed(ctx, "Missing Member", "You need to mention a member to add as staff.", "staff add @user")
                return
            
            added_roles = []
            for role in staff_roles:
                if role not in member.roles:
                    await member.add_roles(role)
                    added_roles.append(role.name)
            
            if added_roles:
                await self.success_embed(ctx, "Staff Role Added", f"{member.mention} now has staff roles: **{', '.join(added_roles)}**", discord.Color.green())
            else:
                await self.error_embed(ctx, "Already Staff", f"{member.mention} already has all staff roles.", None)
        
        # Remove staff role from member
        elif action.lower() == "remove":
            if member is None:
                await self.error_embed(ctx, "Missing Member", "You need to mention a member to remove as staff.", "staff remove @user")
                return
            
            removed_roles = []
            for role in staff_roles:
                if role in member.roles:
                    await member.remove_roles(role)
                    removed_roles.append(role.name)
            
            if removed_roles:
                await self.success_embed(ctx, "Staff Role Removed", f"{member.mention} no longer has staff roles: **{', '.join(removed_roles)}**", discord.Color.red())
            else:
                await self.error_embed(ctx, "Not Staff", f"{member.mention} does not have any staff roles.", None)
        
        else:
            await self.error_embed(ctx, "Invalid Action", "Use `add`, `remove`, or `list`.", "staff add @user")

    # ========== ERROR HANDLER ==========
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing = error.missing_permissions[0] if error.missing_permissions else "unknown"
            embed = discord.Embed(title="❌ Missing Permission", description=f"You need `{missing}` to use `!{ctx.command.name}`.", color=discord.Color.red())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="❌ Missing Argument", description="You are missing a required argument.", color=discord.Color.red())
            embed.add_field(name="📝 Example", value=f"`!{ctx.command.name} {ctx.command.signature if ctx.command.signature else ''}`", inline=False)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="❌ Invalid Argument", description="Please check your command arguments.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            print(f"Unhandled error: {error}")

async def setup(bot):
    await bot.add_cog(Settings(bot))
