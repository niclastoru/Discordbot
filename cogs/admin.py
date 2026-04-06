import discord
from discord.ext import commands
from datetime import datetime
import sqlite3
import aiohttp
import asyncio
import re

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "admin.db"
        self.init_database()
        self.bot.loop.create_task(self.update_status_loop())

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS server_settings (
            guild_id TEXT PRIMARY KEY,
            antinuke_enabled TEXT DEFAULT '0',
            antiraid_enabled TEXT DEFAULT '0',
            vanity_url TEXT,
            rules TEXT,
            welcome_channel TEXT,
            welcome_message TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS disabled_commands (
            guild_id TEXT,
            command_name TEXT,
            PRIMARY KEY (guild_id, command_name)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS reaction_roles (
            guild_id TEXT,
            message_id TEXT,
            emoji TEXT,
            role_id TEXT,
            PRIMARY KEY (guild_id, message_id, emoji)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS auto_responders (
            guild_id TEXT,
            trigger TEXT,
            response TEXT,
            PRIMARY KEY (guild_id, trigger)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS sticky_messages (
            guild_id TEXT,
            channel_id TEXT,
            message_id TEXT,
            content TEXT,
            PRIMARY KEY (guild_id, channel_id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS admin_warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            reason TEXT,
            mod_name TEXT,
            date TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_customize (
            user_id TEXT,
            guild_id TEXT,
            avatar_url TEXT,
            banner_url TEXT,
            bio TEXT,
            PRIMARY KEY (user_id, guild_id)
        )''')
        
        conn.commit()
        conn.close()

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

    def is_command_disabled(self, guild_id, command_name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT 1 FROM disabled_commands WHERE guild_id = ? AND command_name = ?", (str(guild_id), command_name))
        result = c.fetchone()
        conn.close()
        return result is not None

    def disable_command(self, guild_id, command_name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO disabled_commands VALUES (?, ?)", (str(guild_id), command_name))
        conn.commit()
        conn.close()

    def enable_command(self, guild_id, command_name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM disabled_commands WHERE guild_id = ? AND command_name = ?", (str(guild_id), command_name))
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

    async def check_hierarchy(self, ctx, target=None):
        if target and target == ctx.author:
            await self.error_embed(ctx, "Action Failed", "You cannot perform this action on yourself.")
            return False
        return True

    # ========== ACTIVITY ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def activity(self, ctx, activity_type: str = None, *, status: str = None):
        """Changes bot activity. Types: playing, watching, listening, streaming"""
        if activity_type is None or status is None:
            await self.error_embed(ctx, "Missing Arguments", "You need to specify activity type and status.", "activity playing Minecraft")
            return
        
        if activity_type.lower() == "playing":
            activity = discord.Game(name=status)
        elif activity_type.lower() == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status)
        elif activity_type.lower() == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status)
        elif activity_type.lower() == "streaming":
            activity = discord.Streaming(name=status, url="https://twitch.tv/example")
        else:
            await self.error_embed(ctx, "Invalid Type", "Use: playing, watching, listening, streaming", "activity playing Minecraft")
            return
        
        await self.bot.change_presence(activity=activity)
        await self.success_embed(ctx, "Activity Changed", f"Bot is now **{activity_type}** {status}", discord.Color.blue())

    # ========== ANNOUNCE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel = None, *, message: str = None):
        """Sends an announcement to a channel"""
        if channel is None:
            await self.error_embed(ctx, "Missing Channel", "You need to specify a channel.", "announce #general Hello everyone!")
            return
        if message is None:
            await self.error_embed(ctx, "Missing Message", "You need to provide an announcement message.", "announce #general Hello everyone!")
            return
        
        embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_footer(text=f"Announced by {ctx.author.display_name}")
        await channel.send(embed=embed)
        await self.success_embed(ctx, "Announcement Sent", f"Message sent to {channel.mention}", discord.Color.green())

    # ========== ANTINUKE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx, action: str = None):
        """Enables/disables anti-nuke protection"""
        if action is None:
            current = self.get_setting(ctx.guild.id, "antinuke_enabled")
            status = "ENABLED" if current == "1" else "DISABLED"
            embed = discord.Embed(title="🛡️ Anti-Nuke Status", description=f"Currently: **{status}**", color=discord.Color.blue())
            await ctx.send(embed=embed)
            return
        
        if action.lower() == "on":
            self.set_setting(ctx.guild.id, "antinuke_enabled", "1")
            await self.success_embed(ctx, "Anti-Nuke Enabled", "Server is now protected against nukes.", discord.Color.green())
        elif action.lower() == "off":
            self.set_setting(ctx.guild.id, "antinuke_enabled", "0")
            await self.success_embed(ctx, "Anti-Nuke Disabled", "Server protection has been disabled.", discord.Color.red())
        else:
            await self.error_embed(ctx, "Invalid Action", "Use `on` or `off`", "antinuke on")

    # ========== ANTIRAID ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, action: str = None):
        """Enables/disables anti-raid protection"""
        if action is None:
            current = self.get_setting(ctx.guild.id, "antiraid_enabled")
            status = "ENABLED" if current == "1" else "DISABLED"
            embed = discord.Embed(title="🛡️ Anti-Raid Status", description=f"Currently: **{status}**", color=discord.Color.blue())
            await ctx.send(embed=embed)
            return
        
        if action.lower() == "on":
            self.set_setting(ctx.guild.id, "antiraid_enabled", "1")
            await self.success_embed(ctx, "Anti-Raid Enabled", "Server is now protected against raids.", discord.Color.green())
        elif action.lower() == "off":
            self.set_setting(ctx.guild.id, "antiraid_enabled", "0")
            await self.success_embed(ctx, "Anti-Raid Disabled", "Raid protection has been disabled.", discord.Color.red())
        else:
            await self.error_embed(ctx, "Invalid Action", "Use `on` or `off`", "antiraid on")

    # ========== AUTORESPONDER ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def autoresponder(self, ctx, action: str = None, trigger: str = None, *, response: str = None):
        """!autoresponder add <trigger> <response> | remove <trigger> | list"""
        if action is None:
            embed = discord.Embed(title="📋 Auto-Responder Usage", color=discord.Color.blue())
            embed.add_field(name="Add", value="`!autoresponder add hello Hello there!`", inline=False)
            embed.add_field(name="Remove", value="`!autoresponder remove hello`", inline=False)
            embed.add_field(name="List", value="`!autoresponder list`", inline=False)
            await ctx.send(embed=embed)
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if action.lower() == "add" and trigger and response:
            c.execute("INSERT OR REPLACE INTO auto_responders VALUES (?, ?, ?)",
                      (str(ctx.guild.id), trigger.lower(), response))
            conn.commit()
            await self.success_embed(ctx, "Auto-Responder Added", f"`{trigger}` -> `{response}`", discord.Color.green())
        
        elif action.lower() == "remove" and trigger:
            c.execute("DELETE FROM auto_responders WHERE guild_id = ? AND trigger = ?", (str(ctx.guild.id), trigger.lower()))
            conn.commit()
            await self.success_embed(ctx, "Auto-Responder Removed", f"Removed `{trigger}`", discord.Color.green())
        
        elif action.lower() == "list":
            c.execute("SELECT trigger, response FROM auto_responders WHERE guild_id = ?", (str(ctx.guild.id),))
            results = c.fetchall()
            if results:
                lines = [f"`{t}` → {r}" for t, r in results]
                embed = discord.Embed(title="📋 Auto-Responders", description="\n".join(lines[:20]), color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await self.error_embed(ctx, "No Auto-Responders", "No auto-responders have been set up.", "autoresponder add hello Hi!")
        
        else:
            await self.error_embed(ctx, "Invalid Usage", "Use: `add`, `remove`, or `list`", "autoresponder add hello Hi!")
        
        conn.close()

    # ========== CUSTOMIZE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def customize(self, ctx, member: discord.Member = None):
        """Shows customization options for a member"""
        member = member or ctx.author
        embed = discord.Embed(title=f"🎨 Customize {member.display_name}", color=discord.Color.blue())
        embed.add_field(name="Set Avatar", value="`!setavatar @user <url>`", inline=False)
        embed.add_field(name="Set Banner", value="`!setbanner @user <url>`", inline=False)
        embed.add_field(name="Set Bio", value="`!setbio @user <text>`", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setavatar(self, ctx, member: discord.Member = None, url: str = None):
        """Sets custom avatar for a member (bot-side)"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member.", "setavatar @user https://example.com/image.png")
            return
        if url is None:
            await self.error_embed(ctx, "Missing URL", "You need to provide an image URL.", "setavatar @user https://example.com/image.png")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_customize (user_id, guild_id, avatar_url) VALUES (?, ?, ?)",
                  (str(member.id), str(ctx.guild.id), url))
        conn.commit()
        conn.close()
        await self.success_embed(ctx, "Custom Avatar Set", f"{member.mention} now has a custom avatar.", discord.Color.blue())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setbanner(self, ctx, member: discord.Member = None, url: str = None):
        """Sets custom banner for a member (bot-side)"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member.", "setbanner @user https://example.com/banner.png")
            return
        if url is None:
            await self.error_embed(ctx, "Missing URL", "You need to provide an image URL.", "setbanner @user https://example.com/banner.png")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_customize (user_id, guild_id, banner_url) VALUES (?, ?, ?)",
                  (str(member.id), str(ctx.guild.id), url))
        conn.commit()
        conn.close()
        await self.success_embed(ctx, "Custom Banner Set", f"{member.mention} now has a custom banner.", discord.Color.blue())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setbio(self, ctx, member: discord.Member = None, *, bio: str = None):
        """Sets custom bio for a member (bot-side)"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member.", "setbio @user Cool person!")
            return
        if bio is None:
            await self.error_embed(ctx, "Missing Bio", "You need to provide a bio text.", "setbio @user Cool person!")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_customize (user_id, guild_id, bio) VALUES (?, ?, ?)",
                  (str(member.id), str(ctx.guild.id), bio))
        conn.commit()
        conn.close()
        await self.success_embed(ctx, "Custom Bio Set", f"{member.mention} now has a custom bio: {bio}", discord.Color.blue())

    # ========== DISABLECOMMAND ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def disablecommand(self, ctx, command_name: str = None):
        """Disables a command in this server"""
        if command_name is None:
            await self.error_embed(ctx, "Missing Command", "You need to specify a command to disable.", "disablecommand ban")
            return
        
        cmd = self.bot.get_command(command_name.lower())
        if cmd is None:
            await self.error_embed(ctx, "Command Not Found", f"`{command_name}` is not a valid command.", "disablecommand ban")
            return
        
        self.disable_command(ctx.guild.id, command_name.lower())
        await self.success_embed(ctx, "Command Disabled", f"`!{command_name}` has been disabled in this server.", discord.Color.red())

    # ========== DMALL ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def dmall(self, ctx, *, message: str = None):
        """DMs a message to all members (use with caution!)"""
        if message is None:
            await self.error_embed(ctx, "Missing Message", "You need to provide a message to DM.", "dmall Hello everyone!")
            return
        
        confirm_embed = discord.Embed(title="⚠️ Confirm DM All", description=f"This will DM **{len(ctx.guild.members)}** members.\n\nMessage: {message[:100]}\n\nType `yes` to confirm or `no` to cancel.", color=discord.Color.orange())
        await ctx.send(embed=confirm_embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]
        
        try:
            response = await self.bot.wait_for('message', timeout=30.0, check=check)
            if response.content.lower() == "no":
                await self.error_embed(ctx, "Cancelled", "DM All has been cancelled.", None)
                return
        except asyncio.TimeoutError:
            await self.error_embed(ctx, "Timed Out", "You took too long to respond.", None)
            return
        
        sent = 0
        failed = 0
        
        embed = discord.Embed(title="📨 Message from Staff", description=message, color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_footer(text=f"Server: {ctx.guild.name}")
        
        status_msg = await ctx.send("📨 Sending DMs...")
        
        for member in ctx.guild.members:
            if not member.bot:
                try:
                    await member.send(embed=embed)
                    sent += 1
                    await asyncio.sleep(0.5)
                except:
                    failed += 1
        
        await status_msg.edit(content=f"✅ DMs sent to **{sent}** members. Failed: **{failed}**")

    # ========== ENABLECOMMAND ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def enablecommand(self, ctx, command_name: str = None):
        """Enables a disabled command in this server"""
        if command_name is None:
            await self.error_embed(ctx, "Missing Command", "You need to specify a command to enable.", "enablecommand ban")
            return
        
        self.enable_command(ctx.guild.id, command_name.lower())
        await self.success_embed(ctx, "Command Enabled", f"`!{command_name}` has been enabled in this server.", discord.Color.green())

    # ========== FAKEPERMISSIONS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def fakepermissions(self, ctx, member: discord.Member = None, *, permissions: str = None):
        """Simulates permissions for a user (bot-side only)"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member.", "fakepermissions @user Administrator")
            return
        if permissions is None:
            await self.error_embed(ctx, "Missing Permissions", "You need to specify fake permissions.", "fakepermissions @user Administrator")
            return
        
        await self.success_embed(ctx, "Fake Permissions Set", f"{member.mention} now has fake permissions: `{permissions}`\n*This only affects bot commands, not Discord permissions.*", discord.Color.purple())

    # ========== LISTPERMISSIONS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def listpermissions(self, ctx, member: discord.Member = None):
        """Lists all permissions a member has"""
        member = member or ctx.author
        perms = [p.replace('_', ' ').title() for p, v in member.guild_permissions if v]
        
        if not perms:
            embed = discord.Embed(title=f"Permissions of {member.display_name}", description="No permissions", color=discord.Color.blue())
        else:
            embed = discord.Embed(title=f"Permissions of {member.display_name}", description="\n".join(perms[:25]), color=discord.Color.blue())
        
        await ctx.send(embed=embed)

    # ========== NUKE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """Deletes and recreates a channel (clears all messages)"""
        channel = channel or ctx.channel
        
        confirm_embed = discord.Embed(title="⚠️ Confirm Nuke", description=f"This will delete **{channel.mention}** and create a new one.\nType `yes` to confirm or `no` to cancel.", color=discord.Color.red())
        await ctx.send(embed=confirm_embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]
        
        try:
            response = await self.bot.wait_for('message', timeout=30.0, check=check)
            if response.content.lower() == "no":
                await self.error_embed(ctx, "Cancelled", "Nuke has been cancelled.", None)
                return
        except asyncio.TimeoutError:
            await self.error_embed(ctx, "Timed Out", "You took too long to respond.", None)
            return
        
        await ctx.send(f"💣 Nuking {channel.mention}...")
        new_channel = await channel.clone()
        await channel.delete()
        
        embed = discord.Embed(title="💥 Channel Nuked!", description=f"This channel has been nuked by {ctx.author.mention}", color=discord.Color.red())
        await new_channel.send(embed=embed)

    # ========== REACTION-SETUP ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reaction_setup(self, ctx, message_id: str = None, emoji: str = None, role: discord.Role = None):
        """Sets up a reaction role. !reaction-setup <message_id> <emoji> <@role>"""
        if message_id is None or emoji is None or role is None:
            await self.error_embed(ctx, "Missing Arguments", "You need to provide message ID, emoji, and role.", "reaction_setup 1234567890 ✅ @Role")
            return
        
        try:
            message = await ctx.channel.fetch_message(int(message_id))
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO reaction_roles VALUES (?, ?, ?, ?)",
                      (str(ctx.guild.id), message_id, emoji, str(role.id)))
            conn.commit()
            conn.close()
            
            await message.add_reaction(emoji)
            await self.success_embed(ctx, "Reaction Role Set", f"{emoji} → {role.mention}", discord.Color.green())
        except:
            await self.error_embed(ctx, "Setup Failed", "Could not find message or invalid emoji.", "reaction_setup 1234567890 ✅ @Role")

    # ========== REACTIONROLES ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reactionroles(self, ctx):
        """Lists all reaction roles in this server"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT message_id, emoji, role_id FROM reaction_roles WHERE guild_id = ?", (str(ctx.guild.id),))
        results = c.fetchall()
        conn.close()
        
        if not results:
            await self.error_embed(ctx, "No Reaction Roles", "No reaction roles have been set up.", "reaction_setup 1234567890 ✅ @Role")
            return
        
        lines = []
        for msg_id, emoji, role_id in results:
            role = ctx.guild.get_role(int(role_id))
            lines.append(f"📝 Message: `{msg_id}` | {emoji} → {role.mention if role else 'Unknown'}")
        
        embed = discord.Embed(title="🎭 Reaction Roles", description="\n".join(lines[:20]), color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== SERVERRULES ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def serverrules(self, ctx, *, rules: str = None):
        """Sets or shows server rules"""
        if not rules:
            current = self.get_setting(ctx.guild.id, "rules")
            if current:
                embed = discord.Embed(title=f"📜 Rules of {ctx.guild.name}", description=current, color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await self.error_embed(ctx, "No Rules Set", "Use `!serverrules <rules>` to set server rules.", "serverrules Be respectful to everyone")
            return
        
        self.set_setting(ctx.guild.id, "rules", rules)
        await self.success_embed(ctx, "Server Rules Updated", "The server rules have been updated.", discord.Color.green())

    # ========== SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Shows current server settings"""
        antinuke = self.get_setting(ctx.guild.id, "antinuke_enabled") == "1"
        antiraid = self.get_setting(ctx.guild.id, "antiraid_enabled") == "1"
        vanity = self.get_setting(ctx.guild.id, "vanity_url") or "Not set"
        
        embed = discord.Embed(title=f"⚙️ Server Settings - {ctx.guild.name}", color=discord.Color.blue())
        embed.add_field(name="🛡️ Anti-Nuke", value="✅ Enabled" if antinuke else "❌ Disabled", inline=True)
        embed.add_field(name="🛡️ Anti-Raid", value="✅ Enabled" if antiraid else "❌ Disabled", inline=True)
        embed.add_field(name="🔗 Vanity URL", value=vanity, inline=True)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM disabled_commands WHERE guild_id = ?", (str(ctx.guild.id),))
        disabled_count = c.fetchone()[0]
        conn.close()
        
        embed.add_field(name="🚫 Disabled Commands", value=disabled_count, inline=True)
        await ctx.send(embed=embed)

    # ========== BOTSTATUS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def botstatus(self, ctx):
        """Shows bot status and statistics"""
        embed = discord.Embed(title="🤖 Bot Status", color=discord.Color.green(), timestamp=datetime.now())
        embed.add_field(name="📡 Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🖥️ Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="🔧 Commands", value=len(self.bot.commands), inline=True)
        embed.add_field(name="📁 Cogs", value=len(self.bot.cogs), inline=True)
        await ctx.send(embed=embed)

    # ========== STICKYMESSAGE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stickymessage(self, ctx, channel: discord.TextChannel = None, *, message: str = None):
        """Sets a sticky message in a channel (reappears after each message)"""
        channel = channel or ctx.channel
        
        if not message:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM sticky_messages WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(channel.id)))
            conn.commit()
            conn.close()
            await self.success_embed(ctx, "Sticky Message Removed", f"Removed sticky message from {channel.mention}", discord.Color.green())
            return
        
        sticky_msg = await channel.send(message)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO sticky_messages VALUES (?, ?, ?, ?)",
                  (str(ctx.guild.id), str(channel.id), str(sticky_msg.id), message))
        conn.commit()
        conn.close()
        
        await self.success_embed(ctx, "Sticky Message Set", f"Sticky message set in {channel.mention}", discord.Color.green())

    # ========== STRIPSTAFF ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stripstaff(self, ctx, member: discord.Member = None):
        """Removes all staff/admin roles from a member"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member.", "stripstaff @user")
            return
        
        staff_role_names = ["admin", "mod", "staff", "moderator", "owner", "management", "trial mod", "support"]
        removed = []
        
        for role in member.roles[:]:
            if role.name.lower() in staff_role_names:
                await member.remove_roles(role)
                removed.append(role.name)
        
        if removed:
            await self.success_embed(ctx, "Staff Roles Removed", f"Removed from {member.mention}: **{', '.join(removed)}**", discord.Color.red())
        else:
            await self.error_embed(ctx, "No Staff Roles", f"{member.mention} has no staff roles.", "stripstaff @user")

    # ========== UNBANALL ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unbanall(self, ctx):
        """Unbans all banned users from the server"""
        banned = [entry async for entry in ctx.guild.bans()]
        
        if not banned:
            await self.error_embed(ctx, "No Banned Users", "There are no banned users in this server.", None)
            return
        
        confirm_embed = discord.Embed(title="⚠️ Confirm Unban All", description=f"This will unban **{len(banned)}** users.\nType `yes` to confirm or `no` to cancel.", color=discord.Color.orange())
        await ctx.send(embed=confirm_embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]
        
        try:
            response = await self.bot.wait_for('message', timeout=30.0, check=check)
            if response.content.lower() == "no":
                await self.error_embed(ctx, "Cancelled", "Unban All has been cancelled.", None)
                return
        except asyncio.TimeoutError:
            await self.error_embed(ctx, "Timed Out", "You took too long to respond.", None)
            return
        
        unbanned = 0
        for entry in banned:
            try:
                await ctx.guild.unban(entry.user)
                unbanned += 1
                await asyncio.sleep(0.5)
            except:
                pass
        
        await self.success_embed(ctx, "Unban All Complete", f"Unbanned **{unbanned}** out of **{len(banned)}** users.", discord.Color.green())

    # ========== UNJAILALL ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unjailall(self, ctx):
        """Unjails all jailed members"""
        role_name, _ = self.get_jail_settings_from_db(ctx.guild.id) if hasattr(self, 'get_jail_settings_from_db') else ("Jailed", None)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            await self.error_embed(ctx, "No Jail Role", "No jail role found in this server.", "jail_settings @Jailed")
            return
        
        jailed = [m for m in ctx.guild.members if role in m.roles]
        
        if not jailed:
            await self.error_embed(ctx, "No Jailed Members", "There are no jailed members in this server.", None)
            return
        
        for member in jailed:
            await member.remove_roles(role)
        
        await self.success_embed(ctx, "Unjail All Complete", f"Unjailed **{len(jailed)}** members.", discord.Color.green())

    def get_jail_settings_from_db(self, guild_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_name, channel_id FROM jail_settings WHERE guild_id = ?", (str(guild_id),))
        result = c.fetchone()
        conn.close()
        return result if result else ("Jailed", None)

    # ========== VANITY-URL ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def vanity_url(self, ctx, url: str = None):
        """Sets or shows the server's vanity URL"""
        if url:
            self.set_setting(ctx.guild.id, "vanity_url", url)
            await self.success_embed(ctx, "Vanity URL Set", f"Vanity URL set to: `{url}`", discord.Color.green())
        else:
            current = self.get_setting(ctx.guild.id, "vanity_url")
            if current:
                embed = discord.Embed(title="🔗 Vanity URL", description=f"Current vanity URL: `{current}`", color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await self.error_embed(ctx, "No Vanity URL", "No vanity URL has been set.", "vanity_url discord.gg/myserver")

    # ========== VERWARNUNG ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def verwarnung(self, ctx, member: discord.Member = None, *, reason: str = "No reason"):
        """Warns a member (German command)"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "Du musst einen Member erwähnen.", "verwarnung @user Regelverstoß")
            return
        
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO admin_warns (guild_id, user_id, reason, mod_name, date) VALUES (?, ?, ?, ?, ?)",
                  (str(ctx.guild.id), str(member.id), reason, str(ctx.author), date))
        
        c.execute("SELECT COUNT(*) FROM admin_warns WHERE guild_id = ? AND user_id = ?", (str(ctx.guild.id), str(member.id)))
        warn_count = c.fetchone()[0]
        conn.commit()
        conn.close()
        
        embed = discord.Embed(title="⚠️ Verwarnung / Warning", description=f"{member.mention} wurde verwarnt.\n**Grund:** {reason}\n**Anzahl Warnungen:** {warn_count}", color=discord.Color.orange())
        await ctx.send(embed=embed)
        
        try:
            await member.send(f"📢 Du wurdest auf **{ctx.guild.name}** verwarnt.\nGrund: {reason}")
        except:
            pass

    # ========== LISTENERS ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Auto-responder
        c.execute("SELECT response FROM auto_responders WHERE guild_id = ? AND trigger = ?", 
                  (str(message.guild.id), message.content.lower()))
        result = c.fetchone()
        if result:
            await message.channel.send(result[0])
        
        # Sticky message
        c.execute("SELECT message_id, content FROM sticky_messages WHERE guild_id = ? AND channel_id = ?", 
                  (str(message.guild.id), str(message.channel.id)))
        sticky = c.fetchone()
        conn.close()
        
        if sticky:
            try:
                sticky_msg = await message.channel.fetch_message(int(sticky[0]))
                async for msg in message.channel.history(limit=3):
                    if msg.id != sticky_msg.id and msg.id != message.id:
                        await sticky_msg.delete()
                        new_sticky = await message.channel.send(sticky[1])
                        conn2 = sqlite3.connect(self.db_path)
                        c2 = conn2.cursor()
                        c2.execute("UPDATE sticky_messages SET message_id = ? WHERE guild_id = ? AND channel_id = ?",
                                   (str(new_sticky.id), str(message.guild.id), str(message.channel.id)))
                        conn2.commit()
                        conn2.close()
                        break
            except:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_id FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
                  (str(payload.guild_id), str(payload.message_id), payload.emoji.name))
        result = c.fetchone()
        conn.close()
        
        if result:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(int(result[0]))
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_id FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
                  (str(payload.guild_id), str(payload.message_id), payload.emoji.name))
        result = c.fetchone()
        conn.close()
        
        if result:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(int(result[0]))
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.remove_roles(role)

    # ========== STATUS LOOP ==========
    async def update_status_loop(self):
        await self.bot.wait_until_ready()
        statuses = ["!help", "over your server", f"{len(self.bot.guilds)} servers"]
        index = 0
        while not self.bot.is_closed():
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=statuses[index % len(statuses)]))
            index += 1
            await asyncio.sleep(30)

    # ========== COMMAND CHECK ==========
    async def cog_check(self, ctx):
        if self.is_command_disabled(ctx.guild.id, ctx.command.name):
            await self.error_embed(ctx, "Command Disabled", f"`!{ctx.command.name}` has been disabled by an administrator.", None)
            return False
        return True

async def setup(bot):
    await bot.add_cog(Admin(bot))
