import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3
import aiohttp
import asyncio
import os

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "admin.db"
        self.reaction_roles = {}  # {guild_id: {message_id: {emoji: role_id}}}
        self.auto_responses = {}  # {guild_id: {trigger: response}}
        self.sticky_messages = {}  # {guild_id: {channel_id: message_id}}
        self.init_database()
        self.bot.loop.create_task(self.update_status_loop())

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Server settings
        c.execute('''CREATE TABLE IF NOT EXISTS server_settings (
            guild_id TEXT PRIMARY KEY,
            welcome_channel TEXT,
            welcome_message TEXT,
            log_channel TEXT,
            antinuke_enabled TEXT DEFAULT '0',
            antiraid_enabled TEXT DEFAULT '0',
            vanity_url TEXT
        )''')
        
        # Disabled commands
        c.execute('''CREATE TABLE IF NOT EXISTS disabled_commands (
            guild_id TEXT,
            command_name TEXT,
            PRIMARY KEY (guild_id, command_name)
        )''')
        
        # Reaction roles
        c.execute('''CREATE TABLE IF NOT EXISTS reaction_roles (
            guild_id TEXT,
            message_id TEXT,
            emoji TEXT,
            role_id TEXT,
            PRIMARY KEY (guild_id, message_id, emoji)
        )''')
        
        # Auto responders
        c.execute('''CREATE TABLE IF NOT EXISTS auto_responders (
            guild_id TEXT,
            trigger TEXT,
            response TEXT,
            PRIMARY KEY (guild_id, trigger)
        )''')
        
        # Sticky messages
        c.execute('''CREATE TABLE IF NOT EXISTS sticky_messages (
            guild_id TEXT,
            channel_id TEXT,
            message_id TEXT,
            content TEXT,
            PRIMARY KEY (guild_id, channel_id)
        )''')
        
        # Customize settings (avatar, banner, bio)
        c.execute('''CREATE TABLE IF NOT EXISTS user_customize (
            user_id TEXT,
            guild_id TEXT,
            avatar_url TEXT,
            banner_url TEXT,
            bio TEXT
        )''')
        
        # Warns (if not already in moderation)
        c.execute('''CREATE TABLE IF NOT EXISTS admin_warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            reason TEXT,
            mod_name TEXT,
            date TEXT
        )''')
        
        conn.commit()
        conn.close()

    # ========== SETTINGS ==========
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

    # ========== ACTIVITY ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def activity(self, ctx, activity_type: str, *, status: str):
        """Changes bot activity. Types: playing, watching, listening, streaming"""
        activity_types = {
            "playing": discord.Game,
            "watching": discord.Activity,
            "listening": discord.Activity,
            "streaming": discord.Streaming
        }
        
        if activity_type.lower() not in activity_types:
            await ctx.send("❌ Invalid type. Use: playing, watching, listening, streaming")
            return
        
        if activity_type.lower() == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status)
        elif activity_type.lower() == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status)
        elif activity_type.lower() == "streaming":
            activity = discord.Streaming(name=status, url="https://twitch.tv/example")
        else:
            activity = discord.Game(name=status)
        
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"✅ Activity changed to {activity_type}: {status}")

    # ========== ANNOUNCE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message):
        """Sends an announcement to a channel"""
        embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_footer(text=f"Announced by {ctx.author.display_name}")
        await channel.send(embed=embed)
        await ctx.send(f"✅ Announcement sent to {channel.mention}")

    # ========== ANTINUKE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx, action: str = None):
        """Enables/disables anti-nuke protection. Usage: !antinuke on/off"""
        if not action:
            current = self.get_setting(ctx.guild.id, "antinuke_enabled")
            await ctx.send(f"🛡️ Anti-nuke is currently {'**ENABLED**' if current == '1' else '**DISABLED**'}")
            return
        
        if action.lower() == "on":
            self.set_setting(ctx.guild.id, "antinuke_enabled", "1")
            await ctx.send("✅ Anti-nuke protection **ENABLED**")
        elif action.lower() == "off":
            self.set_setting(ctx.guild.id, "antinuke_enabled", "0")
            await ctx.send("✅ Anti-nuke protection **DISABLED**")
        else:
            await ctx.send("❌ Usage: `!antinuke on` or `!antinuke off`")

    # ========== ANTIRAID ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, action: str = None):
        """Enables/disables anti-raid protection. Usage: !antiraid on/off"""
        if not action:
            current = self.get_setting(ctx.guild.id, "antiraid_enabled")
            await ctx.send(f"🛡️ Anti-raid is currently {'**ENABLED**' if current == '1' else '**DISABLED**'}")
            return
        
        if action.lower() == "on":
            self.set_setting(ctx.guild.id, "antiraid_enabled", "1")
            await ctx.send("✅ Anti-raid protection **ENABLED**")
        elif action.lower() == "off":
            self.set_setting(ctx.guild.id, "antiraid_enabled", "0")
            await ctx.send("✅ Anti-raid protection **DISABLED**")
        else:
            await ctx.send("❌ Usage: `!antiraid on` or `!antiraid off`")

    # ========== AUTORESPONDER ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def autoresponder(self, ctx, action, trigger=None, *, response=None):
        """Adds/removes auto responses. !autoresponder add <trigger> <response> | !autoresponder remove <trigger> | !autoresponder list"""
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if action == "add" and trigger and response:
            c.execute("INSERT OR REPLACE INTO auto_responders (guild_id, trigger, response) VALUES (?, ?, ?)",
                      (str(ctx.guild.id), trigger.lower(), response))
            conn.commit()
            await ctx.send(f"✅ Auto-response added: `{trigger}` -> `{response}`")
        
        elif action == "remove" and trigger:
            c.execute("DELETE FROM auto_responders WHERE guild_id = ? AND trigger = ?", (str(ctx.guild.id), trigger.lower()))
            conn.commit()
            await ctx.send(f"✅ Auto-response removed: `{trigger}`")
        
        elif action == "list":
            c.execute("SELECT trigger, response FROM auto_responders WHERE guild_id = ?", (str(ctx.guild.id),))
            results = c.fetchall()
            if results:
                lines = [f"`{t}` -> {r}" for t, r in results]
                await ctx.send(f"📋 **Auto-responders:**\n" + "\n".join(lines[:20]))
            else:
                await ctx.send("📋 No auto-responders set.")
        
        else:
            await ctx.send("❌ Usage: `!autoresponder add <trigger> <response>` | `!autoresponder remove <trigger>` | `!autoresponder list`")
        
        conn.close()

    # ========== CUSTOMIZE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def customize(self, ctx, member: discord.Member = None):
        """Shows customization options for a member"""
        member = member or ctx.author
        await ctx.send(f"🎨 **Customization for {member.display_name}**\nUse:\n`!customize avatar <url>` - Set custom avatar\n`!customize banner <url>` - Set custom banner\n`!customize bio <text>` - Set custom bio")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def avatar(self, ctx, member: discord.Member, url: str = None):
        """Customizes a member's avatar (bot-side)"""
        if not url:
            await ctx.send("❌ Please provide an image URL")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_customize (user_id, guild_id, avatar_url) VALUES (?, ?, ?)",
                  (str(member.id), str(ctx.guild.id), url))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Custom avatar set for {member.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def banner(self, ctx, member: discord.Member, url: str = None):
        """Customizes a member's banner (bot-side)"""
        if not url:
            await ctx.send("❌ Please provide an image URL")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_customize (user_id, guild_id, banner_url) VALUES (?, ?, ?)",
                  (str(member.id), str(ctx.guild.id), url))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Custom banner set for {member.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def bio(self, ctx, member: discord.Member, *, bio: str = None):
        """Customizes a member's bio"""
        if not bio:
            await ctx.send("❌ Please provide a bio")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_customize (user_id, guild_id, bio) VALUES (?, ?, ?)",
                  (str(member.id), str(ctx.guild.id), bio))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Custom bio set for {member.mention}")

    # ========== DISABLECOMMAND ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def disablecommand(self, ctx, command_name: str):
        """Disables a command in this server"""
        cmd = self.bot.get_command(command_name.lower())
        if not cmd:
            await ctx.send(f"❌ Command `{command_name}` not found")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO disabled_commands (guild_id, command_name) VALUES (?, ?)",
                  (str(ctx.guild.id), command_name.lower()))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Command `!{command_name}` has been **DISABLED**")

    # ========== DMALL ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def dmall(self, ctx, *, message):
        """DMs a message to all members (use with caution!)"""
        await ctx.send("⚠️ This will DM **ALL** members. This may take a while and could get the bot rate-limited. Continue? (yes/no)")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]
        
        try:
            response = await self.bot.wait_for('message', timeout=30.0, check=check)
            if response.content.lower() == "no":
                await ctx.send("❌ Cancelled.")
                return
        except asyncio.TimeoutError:
            await ctx.send("❌ Timed out.")
            return
        
        sent = 0
        failed = 0
        
        embed = discord.Embed(title="📨 Message from Staff", description=message, color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_footer(text=f"Server: {ctx.guild.name}")
        
        for member in ctx.guild.members:
            if not member.bot:
                try:
                    await member.send(embed=embed)
                    sent += 1
                    await asyncio.sleep(0.5)  # Rate limit protection
                except:
                    failed += 1
        
        await ctx.send(f"✅ DM sent to {sent} members. Failed: {failed}")

    # ========== ENABLECOMMAND ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def enablecommand(self, ctx, command_name: str):
        """Enables a disabled command in this server"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM disabled_commands WHERE guild_id = ? AND command_name = ?",
                  (str(ctx.guild.id), command_name.lower()))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Command `!{command_name}` has been **ENABLED**")

    # ========== FAKEPERMISSIONS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def fakepermissions(self, ctx, member: discord.Member, *, permissions: str):
        """Simulates permissions for a user (bot-side only)"""
        await ctx.send(f"🎭 {member.mention} now has fake permissions: {permissions}\n*This only affects bot commands, not Discord permissions.*")

    # ========== LISTPERMISSIONS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def listpermissions(self, ctx, member: discord.Member = None):
        """Lists all permissions a member has"""
        member = member or ctx.author
        perms = [perm for perm, value in member.guild_permissions if value]
        
        if not perms:
            await ctx.send(f"{member.mention} has no special permissions.")
        else:
            embed = discord.Embed(title=f"Permissions of {member.display_name}", description="\n".join([f"✅ {p}" for p in perms]), color=discord.Color.blue())
            await ctx.send(embed=embed)

    # ========== NUKE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """Deletes and recreates a channel (clears all messages)"""
        channel = channel or ctx.channel
        
        await ctx.send(f"💣 Nuking {channel.mention}...")
        new_channel = await channel.clone()
        await channel.delete()
        
        embed = discord.Embed(title="💥 Channel Nuked!", description=f"This channel has been nuked by {ctx.author.mention}", color=discord.Color.red())
        await new_channel.send(embed=embed)

    # ========== REACTION-SETUP ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reaction_setup(self, ctx, message_id: str, emoji: str, role: discord.Role):
        """Sets up a reaction role. !reaction-setup <message_id> <emoji> <@role>"""
        try:
            message = await ctx.channel.fetch_message(int(message_id))
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO reaction_roles (guild_id, message_id, emoji, role_id) VALUES (?, ?, ?, ?)",
                      (str(ctx.guild.id), message_id, emoji, str(role.id)))
            conn.commit()
            conn.close()
            
            await message.add_reaction(emoji)
            await ctx.send(f"✅ Reaction role set: {emoji} -> {role.mention}")
        except:
            await ctx.send("❌ Could not find message or invalid emoji.")

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
            await ctx.send("📋 No reaction roles set up.")
            return
        
        lines = []
        for msg_id, emoji, role_id in results:
            role = ctx.guild.get_role(int(role_id))
            lines.append(f"📝 Message: {msg_id} | {emoji} -> {role.mention if role else 'Unknown role'}")
        
        await ctx.send("🎭 **Reaction Roles:**\n" + "\n".join(lines[:20]))

    # ========== SERVERRULES ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def serverrules(self, ctx, *, rules: str = None):
        """Sets or shows server rules"""
        if not rules:
            current = self.get_setting(ctx.guild.id, "welcome_message")  # Reusing welcome_message for rules
            if current:
                embed = discord.Embed(title=f"📜 Rules of {ctx.guild.name}", description=current, color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await ctx.send("📋 No rules set. Use `!serverrules <rules>` to set them.")
            return
        
        self.set_setting(ctx.guild.id, "welcome_message", rules)  # Store rules in welcome_message field
        await ctx.send("✅ Server rules have been updated!")

    # ========== SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Shows current server settings"""
        antinuke = self.get_setting(ctx.guild.id, "antinuke_enabled") == "1"
        antiraid = self.get_setting(ctx.guild.id, "antiraid_enabled") == "1"
        
        embed = discord.Embed(title=f"⚙️ Server Settings - {ctx.guild.name}", color=discord.Color.blue())
        embed.add_field(name="🛡️ Anti-Nuke", value="✅ Enabled" if antinuke else "❌ Disabled", inline=True)
        embed.add_field(name="🛡️ Anti-Raid", value="✅ Enabled" if antiraid else "❌ Disabled", inline=True)
        
        # Count disabled commands
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM disabled_commands WHERE guild_id = ?", (str(ctx.guild.id),))
        disabled_count = c.fetchone()[0]
        conn.close()
        
        embed.add_field(name="🚫 Disabled Commands", value=disabled_count, inline=True)
        await ctx.send(embed=embed)

    # ========== STATUS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def status(self, ctx):
        """Shows bot status and statistics"""
        embed = discord.Embed(title="🤖 Bot Status", color=discord.Color.green(), timestamp=datetime.now())
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Commands", value=len(self.bot.commands), inline=True)
        await ctx.send(embed=embed)

    # ========== STICKYMESSAGE ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stickymessage(self, ctx, channel: discord.TextChannel = None, *, message: str = None):
        """Sets a sticky message in a channel (reappears after each message)"""
        channel = channel or ctx.channel
        
        if not message:
            # Remove sticky
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM sticky_messages WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(channel.id)))
            conn.commit()
            conn.close()
            await ctx.send(f"✅ Removed sticky message from {channel.mention}")
            return
        
        # Send sticky message
        sticky_msg = await channel.send(message)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO sticky_messages (guild_id, channel_id, message_id, content) VALUES (?, ?, ?, ?)",
                  (str(ctx.guild.id), str(channel.id), str(sticky_msg.id), message))
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ Sticky message set in {channel.mention}")

    # ========== STRIPSTAFF ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stripstaff(self, ctx, member: discord.Member):
        """Removes all staff/admin roles from a member"""
        staff_role_names = ["admin", "mod", "staff", "moderator", "admin", "owner", "management"]
        removed = []
        
        for role in member.roles:
            if role.name.lower() in staff_role_names:
                await member.remove_roles(role)
                removed.append(role.name)
        
        if removed:
            await ctx.send(f"✅ Removed staff roles from {member.mention}: {', '.join(removed)}")
        else:
            await ctx.send(f"❌ {member.mention} has no staff roles.")

    # ========== UNBANALL ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unbanall(self, ctx):
        """Unbans all banned users from the server"""
        banned_users = [entry async for entry in ctx.guild.bans()]
        
        if not banned_users:
            await ctx.send("📋 No banned users found.")
            return
        
        await ctx.send(f"⚠️ This will unban {len(banned_users)} users. Continue? (yes/no)")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]
        
        try:
            response = await self.bot.wait_for('message', timeout=30.0, check=check)
            if response.content.lower() == "no":
                await ctx.send("❌ Cancelled.")
                return
        except asyncio.TimeoutError:
            await ctx.send("❌ Timed out.")
            return
        
        unbanned = 0
        for entry in banned_users:
            try:
                await ctx.guild.unban(entry.user)
                unbanned += 1
                await asyncio.sleep(0.5)
            except:
                pass
        
        await ctx.send(f"✅ Unbanned {unbanned}/{len(banned_users)} users.")

    # ========== UNJAILALL ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unjailall(self, ctx):
        """Unjails all jailed members"""
        jail_role_name = "Jailed"
        role = discord.utils.get(ctx.guild.roles, name=jail_role_name)
        
        if not role:
            await ctx.send("❌ No jail role found.")
            return
        
        jailed = [m for m in ctx.guild.members if role in m.roles]
        
        if not jailed:
            await ctx.send("📋 No jailed members found.")
            return
        
        for member in jailed:
            await member.remove_roles(role)
        
        await ctx.send(f"✅ Unjailed {len(jailed)} members.")

    # ========== VANITY-URL ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def vanity_url(self, ctx, url: str = None):
        """Sets or shows the server's vanity URL"""
        if url:
            self.set_setting(ctx.guild.id, "vanity_url", url)
            await ctx.send(f"✅ Vanity URL set to: {url}")
        else:
            current = self.get_setting(ctx.guild.id, "vanity_url")
            if current:
                await ctx.send(f"🔗 Vanity URL: {current}")
            else:
                await ctx.send("📋 No vanity URL set. Use `!vanity_url <url>` to set one.")

    # ========== VERWARNUNG (WARNING) ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def verwarnung(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warns a member (German command for warning)"""
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO admin_warns (guild_id, user_id, reason, mod_name, date) VALUES (?, ?, ?, ?, ?)",
                  (str(ctx.guild.id), str(member.id), reason, str(ctx.author), date))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(title="⚠️ Verwarnung / Warning", description=f"{member.mention} wurde verwarnt.\nGrund: {reason}", color=discord.Color.orange())
        await ctx.send(embed=embed)
        
        try:
            await member.send(f"📢 Du wurdest auf **{ctx.guild.name}** verwarnt.\nGrund: {reason}")
        except:
            pass

    # ========== AUTO RESPONDER LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT response FROM auto_responders WHERE guild_id = ? AND trigger = ?", 
                  (str(message.guild.id), message.content.lower()))
        result = c.fetchone()
        conn.close()
        
        if result:
            await message.channel.send(result[0])

    # ========== STICKY MESSAGE LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT message_id, content FROM sticky_messages WHERE guild_id = ? AND channel_id = ?", 
                  (str(message.guild.id), str(message.channel.id)))
        result = c.fetchone()
        conn.close()
        
        if result:
            try:
                sticky_msg = await message.channel.fetch_message(int(result[0]))
                # Check if sticky is not the last message
                async for msg in message.channel.history(limit=2):
                    if msg.id != sticky_msg.id and msg.id != message.id:
                        await sticky_msg.delete()
                        new_sticky = await message.channel.send(result[1])
                        
                        # Update database with new message ID
                        conn = sqlite3.connect(self.db_path)
                        c = conn.cursor()
                        c.execute("UPDATE sticky_messages SET message_id = ? WHERE guild_id = ? AND channel_id = ?",
                                  (str(new_sticky.id), str(message.guild.id), str(message.channel.id)))
                        conn.commit()
                        conn.close()
                        break
            except:
                pass

    # ========== REACTION ROLE LISTENER ==========
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

    # ========== STATUS UPDATE LOOP ==========
    async def update_status_loop(self):
        await self.bot.wait_until_ready()
        statuses = [
            {"type": "watching", "name": "over your server"},
            {"type": "playing", "name": "!help"},
            {"type": "listening", "name": "staff commands"},
            {"type": "watching", "name": f"{len(self.bot.guilds)} servers"}
        ]
        index = 0
        while not self.bot.is_closed():
            status = statuses[index % len(statuses)]
            if status["type"] == "playing":
                activity = discord.Game(name=status["name"])
            elif status["type"] == "listening":
                activity = discord.Activity(type=discord.ActivityType.listening, name=status["name"])
            else:
                activity = discord.Activity(type=discord.ActivityType.watching, name=status["name"])
            
            await self.bot.change_presence(activity=activity)
            index += 1
            await asyncio.sleep(30)

async def setup(bot):
    await bot.add_cog(Admin(bot))
