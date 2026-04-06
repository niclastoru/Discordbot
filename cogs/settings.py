import discord
from discord.ext import commands
import sqlite3

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "settings.db"
        self.init_database()
        print("✅ Settings Cog geladen!")

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS jail_settings (
            guild_id TEXT PRIMARY KEY,
            role_id TEXT,
            channel_id TEXT,
            jail_message TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS staff_roles (
            guild_id TEXT,
            role_id TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS whitelist_roles (
            guild_id TEXT,
            role_id TEXT
        )''')
        conn.commit()
        conn.close()
        print("✅ Settings Datenbank initialisiert!")

    async def error_embed(self, ctx, title, desc, example=None):
        embed = discord.Embed(title=f"❌ {title}", description=desc, color=discord.Color.red())
        if example:
            embed.add_field(name="📝 Example", value=f"`{example}`", inline=False)
        await ctx.send(embed=embed)

    async def success_embed(self, ctx, title, desc):
        embed = discord.Embed(title=f"✅ {title}", description=desc, color=discord.Color.green())
        await ctx.send(embed=embed)

    # ========== JAIL SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx, role: discord.Role = None, channel: discord.TextChannel = None):
        """Set jail role and channel. Usage: !jail_settings @Jailed #jail"""
        if role is None and channel is None:
            await self.error_embed(ctx, "Missing Arguments", "You need to provide a role or channel.", "jail_settings @Jailed #jail")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if role:
            c.execute("INSERT OR REPLACE INTO jail_settings (guild_id, role_id) VALUES (?, ?)", (str(ctx.guild.id), str(role.id)))
            await self.success_embed(ctx, "Jail Role Set", f"{role.mention} is now the jail role.")
        
        if channel:
            c.execute("INSERT OR REPLACE INTO jail_settings (guild_id, channel_id) VALUES (?, ?)", (str(ctx.guild.id), str(channel.id)))
            await self.success_embed(ctx, "Jail Channel Set", f"{channel.mention} is now the jail channel.")
        
        conn.commit()
        conn.close()

    # ========== SETTINGS (Übersicht) ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Show all server settings"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_id, channel_id, jail_message FROM jail_settings WHERE guild_id = ?", (str(ctx.guild.id),))
        result = c.fetchone()
        
        c.execute("SELECT role_id FROM staff_roles WHERE guild_id = ?", (str(ctx.guild.id),))
        staff_roles = [row[0] for row in c.fetchall()]
        
        c.execute("SELECT role_id FROM whitelist_roles WHERE guild_id = ?", (str(ctx.guild.id),))
        whitelist_roles = [row[0] for row in c.fetchall()]
        conn.close()
        
        embed = discord.Embed(title=f"⚙️ Server Settings - {ctx.guild.name}", color=discord.Color.blue())
        
        if result:
            role = ctx.guild.get_role(int(result[0])) if result[0] else None
            channel = ctx.guild.get_channel(int(result[1])) if result[1] else None
            embed.add_field(name="🔒 Jail Role", value=role.mention if role else "Not set", inline=True)
            embed.add_field(name="🔒 Jail Channel", value=channel.mention if channel else "Not set", inline=True)
            embed.add_field(name="📝 Jail Message", value="Custom" if result[2] else "Default", inline=True)
        else:
            embed.add_field(name="🔒 Jail Settings", value="Not configured", inline=True)
        
        if staff_roles:
            roles = [ctx.guild.get_role(int(rid)) for rid in staff_roles if ctx.guild.get_role(int(rid))]
            embed.add_field(name="👔 Staff Roles", value=", ".join([r.mention for r in roles]) or "None", inline=False)
        else:
            embed.add_field(name="👔 Staff Roles", value="No staff roles set", inline=False)
        
        if whitelist_roles:
            roles = [ctx.guild.get_role(int(rid)) for rid in whitelist_roles if ctx.guild.get_role(int(rid))]
            embed.add_field(name="✅ Whitelist Roles", value=", ".join([r.mention for r in roles]) or "None", inline=False)
        
        await ctx.send(embed=embed)

    # ========== SETTINGSSTAFF ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstaff(self, ctx, action: str, role: discord.Role):
        """Add/remove staff roles: !settingsstaff add @role | !settingsstaff remove @role"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if action.lower() == "add":
            c.execute("INSERT OR IGNORE INTO staff_roles (guild_id, role_id) VALUES (?, ?)", (str(ctx.guild.id), str(role.id)))
            await self.success_embed(ctx, "Staff Role Added", f"{role.mention} added to staff roles.")
        elif action.lower() == "remove":
            c.execute("DELETE FROM staff_roles WHERE guild_id = ? AND role_id = ?", (str(ctx.guild.id), str(role.id)))
            await self.success_embed(ctx, "Staff Role Removed", f"{role.mention} removed from staff roles.")
        else:
            await self.error_embed(ctx, "Invalid Action", "Use `add` or `remove`.", "settingsstaff add @Moderator")
            return
        
        conn.commit()
        conn.close()

    # ========== SETTINGSSTAFFLIST ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstafflist(self, ctx):
        """List all staff roles"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_id FROM staff_roles WHERE guild_id = ?", (str(ctx.guild.id),))
        results = c.fetchall()
        conn.close()
        
        if not results:
            await self.error_embed(ctx, "No Staff Roles", "No staff roles configured.", "settingsstaff add @Moderator")
            return
        
        roles = []
        for row in results:
            role = ctx.guild.get_role(int(row[0]))
            if role:
                roles.append(role.mention)
        
        embed = discord.Embed(title="👔 Staff Roles", description="\n".join(roles), color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== SETTINGSSTAFFWHITELIST ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settingsstaffwhitelist(self, ctx, action: str, role: discord.Role):
        """Add/remove whitelist roles: !settingsstaffwhitelist add @role | remove @role"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if action.lower() == "add":
            c.execute("INSERT OR IGNORE INTO whitelist_roles (guild_id, role_id) VALUES (?, ?)", (str(ctx.guild.id), str(role.id)))
            await self.success_embed(ctx, "Whitelist Role Added", f"{role.mention} added to whitelist.")
        elif action.lower() == "remove":
            c.execute("DELETE FROM whitelist_roles WHERE guild_id = ? AND role_id = ?", (str(ctx.guild.id), str(role.id)))
            await self.success_embed(ctx, "Whitelist Role Removed", f"{role.mention} removed from whitelist.")
        else:
            await self.error_embed(ctx, "Invalid Action", "Use `add` or `remove`.", "settingsstaffwhitelist add @Trusted")
            return
        
        conn.commit()
        conn.close()

    # ========== STAFF ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def staff(self, ctx, action: str, member: discord.Member = None):
        """Manage staff: !staff add @user | !staff remove @user | !staff list"""
        
        if action.lower() == "list":
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT role_id FROM staff_roles WHERE guild_id = ?", (str(ctx.guild.id),))
            staff_role_ids = [row[0] for row in c.fetchall()]
            conn.close()
            
            if not staff_role_ids:
                await self.error_embed(ctx, "No Staff Roles", "No staff roles configured.", "settingsstaff add @Moderator")
                return
            
            staff_roles = [ctx.guild.get_role(int(rid)) for rid in staff_role_ids if ctx.guild.get_role(int(rid))]
            staff_members = []
            
            for m in ctx.guild.members:
                for role in staff_roles:
                    if role in m.roles:
                        staff_members.append(f"• {m.mention}")
                        break
            
            if staff_members:
                embed = discord.Embed(title="👔 Staff Members", description="\n".join(staff_members), color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await self.error_embed(ctx, "No Staff Members", "No members have staff roles.", None)
            return
        
        if member is None:
            await self.error_embed(ctx, "Missing Member", "Please mention a member.", f"staff {action} @user")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_id FROM staff_roles WHERE guild_id = ?", (str(ctx.guild.id),))
        staff_role_ids = [row[0] for row in c.fetchall()]
        conn.close()
        
        if not staff_role_ids:
            await self.error_embed(ctx, "No Staff Roles", "No staff roles configured.", "settingsstaff add @Moderator")
            return
        
        staff_roles = [ctx.guild.get_role(int(rid)) for rid in staff_role_ids if ctx.guild.get_role(int(rid))]
        
        if action.lower() == "add":
            added = []
            for role in staff_roles:
                if role not in member.roles:
                    await member.add_roles(role)
                    added.append(role.name)
            if added:
                await self.success_embed(ctx, "Staff Added", f"{member.mention} is now staff: {', '.join(added)}")
            else:
                await self.error_embed(ctx, "Already Staff", f"{member.mention} already has staff roles.", None)
        
        elif action.lower() == "remove":
            removed = []
            for role in staff_roles:
                if role in member.roles:
                    await member.remove_roles(role)
                    removed.append(role.name)
            if removed:
                await self.success_embed(ctx, "Staff Removed", f"{member.mention} is no longer staff: {', '.join(removed)}")
            else:
                await self.error_embed(ctx, "Not Staff", f"{member.mention} does not have staff roles.", None)
        
        else:
            await self.error_embed(ctx, "Invalid Action", "Use `add`, `remove`, or `list`.", "staff add @user")

    # ========== SETTINGS_JAILMSG ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings_jailmsg(self, ctx, *, message: str = None):
        """Set custom jail message. Use {user} and {reason}"""
        if message is None:
            await self.error_embed(ctx, "Missing Message", "Please provide a jail message.", "settings_jailmsg {user} was jailed for {reason}")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO jail_settings (guild_id, jail_message) VALUES (?, ?)", (str(ctx.guild.id), message))
        conn.commit()
        conn.close()
        
        await self.success_embed(ctx, "Jail Message Set", f"```{message}```\nUse `{{user}}` for user, `{{reason}}` for reason.")

async def setup(bot):
    print("🔥 Settings.py wird geladen...")
    await bot.add_cog(Settings(bot))
    print("✅ Settings.py erfolgreich geladen!")
