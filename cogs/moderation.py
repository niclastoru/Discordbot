import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3
import os

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "moderation.db"
        self.init_database()
        self.load_settings()

    def init_database(self):
        """Initialisiert alle Tabellen für Multi-Server"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Tabelle für Warns
        c.execute('''CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            reason TEXT,
            mod_name TEXT,
            date TEXT
        )''')
        
        # Tabelle für Jail-Settings pro Server
        c.execute('''CREATE TABLE IF NOT EXISTS jail_settings (
            guild_id TEXT PRIMARY KEY,
            role_name TEXT,
            channel_id TEXT
        )''')
        
        # Tabelle für Log-Channel pro Server
        c.execute('''CREATE TABLE IF NOT EXISTS log_settings (
            guild_id TEXT PRIMARY KEY,
            channel_id TEXT
        )''')
        
        # Tabelle für Wordfilter pro Server
        c.execute('''CREATE TABLE IF NOT EXISTS wordfilters (
            guild_id TEXT,
            word TEXT,
            PRIMARY KEY (guild_id, word)
        )''')
        
        conn.commit()
        conn.close()

    def load_settings(self):
        """Lade Settings werden bei Bedarf aus DB geladen"""
        pass

    def get_warns(self, guild_id, user_id):
        """Holt alle Warns eines Users auf einem Server"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT reason, mod_name, date FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY id DESC", (str(guild_id), str(user_id)))
        result = c.fetchall()
        conn.close()
        return [{"reason": r[0], "mod": r[1], "date": r[2]} for r in result]

    def add_warn(self, guild_id, user_id, reason, mod_name, date):
        """Fügt einen Warn hinzu"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO warns (guild_id, user_id, reason, mod_name, date) VALUES (?, ?, ?, ?, ?)",
                  (str(guild_id), str(user_id), reason, mod_name, date))
        conn.commit()
        conn.close()

    def clear_warns(self, guild_id, user_id):
        """Löscht alle Warns eines Users auf einem Server"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM warns WHERE guild_id = ? AND user_id = ?", (str(guild_id), str(user_id)))
        conn.commit()
        conn.close()

    # ========== JAIL SETTINGS ==========
    def get_jail_settings(self, guild_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role_name, channel_id FROM jail_settings WHERE guild_id = ?", (str(guild_id),))
        result = c.fetchone()
        conn.close()
        return result if result else ("Jailed", None)

    def set_jail_settings(self, guild_id, role_name=None, channel_id=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        existing = self.get_jail_settings(guild_id)
        new_role = role_name if role_name else existing[0]
        new_channel = channel_id if channel_id else existing[1]
        c.execute("INSERT OR REPLACE INTO jail_settings (guild_id, role_name, channel_id) VALUES (?, ?, ?)",
                  (str(guild_id), new_role, new_channel))
        conn.commit()
        conn.close()

    # ========== LOG SETTINGS ==========
    def get_log_channel(self, guild_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT channel_id FROM log_settings WHERE guild_id = ?", (str(guild_id),))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def set_log_channel(self, guild_id, channel_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO log_settings (guild_id, channel_id) VALUES (?, ?)",
                  (str(guild_id), channel_id))
        conn.commit()
        conn.close()

    # ========== WORD FILTER ==========
    def get_wordfilter_words(self, guild_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT word FROM wordfilters WHERE guild_id = ?", (str(guild_id),))
        result = [row[0] for row in c.fetchall()]
        conn.close()
        return result

    def add_wordfilter_word(self, guild_id, word):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO wordfilters (guild_id, word) VALUES (?, ?)", (str(guild_id), word.lower()))
        conn.commit()
        conn.close()

    def remove_wordfilter_word(self, guild_id, word):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM wordfilters WHERE guild_id = ? AND word = ?", (str(guild_id), word.lower()))
        conn.commit()
        conn.close()

    # ========== BAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Bans a member"""
        await member.ban(reason=reason)
        embed = discord.Embed(title="✅ Banned", description=f"{member.mention} has been banned.\nReason: {reason}", color=discord.Color.red())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Ban", member, reason)

    # ========== CLEARNICK ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def clearnick(self, ctx, member: discord.Member):
        """Clears a member's nickname"""
        await member.edit(nick=None)
        embed = discord.Embed(title="🧹 Nickname cleared", description=f"{member.mention}'s nickname has been reset", color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== DRAG ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def drag(self, ctx, member: discord.Member, target_channel: discord.VoiceChannel):
        """Drags a member to another voice channel"""
        if member.voice and member.voice.channel:
            await member.move_to(target_channel)
            embed = discord.Embed(title="🎤 Member moved", description=f"{member.mention} moved to {target_channel.mention}", color=discord.Color.purple())
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Member is not in a voice channel.")

    # ========== HISTORY ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def history(self, ctx, member: discord.Member, limit: int = 10):
        """Shows warning history of a member"""
        warns = self.get_warns(ctx.guild.id, member.id)
        if not warns:
            await ctx.send(f"{member.mention} has no warnings.")
            return
        
        warns = warns[:limit]
        embed = discord.Embed(title=f"⚠️ Warning History of {member.display_name}", color=discord.Color.orange())
        
        for i, warn in enumerate(warns, 1):
            embed.add_field(name=f"Warning {i}", value=f"Reason: {warn['reason']}\nBy: {warn['mod']}\nDate: {warn['date']}", inline=False)
        
        await ctx.send(embed=embed)

    # ========== HISTORYCHANNEL ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def historychannel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel for moderation logs"""
        if channel:
            self.set_log_channel(ctx.guild.id, channel.id)
            embed = discord.Embed(title="📝 Log channel set", description=f"Logs will be sent to {channel.mention}", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            self.set_log_channel(ctx.guild.id, None)
            await ctx.send("✅ Log channel disabled.")

    # ========== JAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def jail(self, ctx, member: discord.Member, *, reason=None):
        """Puts a member in jail"""
        role_name, jail_channel_id = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            role = await ctx.guild.create_role(name=role_name, permissions=discord.Permissions(send_messages=False, add_reactions=False, speak=False))
            await ctx.send(f"⚠️ Role `{role_name}` was automatically created.")
        
        await member.add_roles(role)
        
        if jail_channel_id:
            jail_channel = ctx.guild.get_channel(int(jail_channel_id))
            if jail_channel:
                await jail_channel.send(f"{member.mention} has been jailed. Reason: {reason}")
        
        embed = discord.Embed(title="🔒 Jailed", description=f"{member.mention} has been put in jail.\nReason: {reason}", color=discord.Color.red())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Jail", member, reason)

    # ========== JAIL-LIST ==========
    @commands.command()
    async def jail_list(self, ctx):
        """Shows all jailed members"""
        role_name, _ = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            await ctx.send("❌ No jail role found.")
            return
        
        jailed_members = [member for member in ctx.guild.members if role in member.roles]
        
        if not jailed_members:
            await ctx.send("🔓 No one is in jail.")
        else:
            member_list = "\n".join([f"{member.mention} - {member.name}" for member in jailed_members])
            embed = discord.Embed(title="🔒 Jailed Members", description=member_list, color=discord.Color.red())
            await ctx.send(embed=embed)

    # ========== JAIL-SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx, role_name: str = None, channel: discord.TextChannel = None):
        """Sets jail role and jail channel"""
        if role_name or channel:
            self.set_jail_settings(ctx.guild.id, role_name, channel.id if channel else None)
            await ctx.send(f"✅ Jail settings updated.\nRole: {role_name or 'unchanged'}\nChannel: {channel.mention if channel else 'unchanged'}")
        else:
            current_role, current_channel = self.get_jail_settings(ctx.guild.id)
            await ctx.send(f"📋 Current jail settings:\nRole: `{current_role}`\nChannel: {f'<#{current_channel}>' if current_channel else 'Not set'}")

    # ========== KICK ==========
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kicks a member"""
        await member.kick(reason=reason)
        embed = discord.Embed(title="✅ Kicked", description=f"{member.mention} has been kicked.\nReason: {reason}", color=discord.Color.orange())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Kick", member, reason)

    # ========== LOCK ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Locks a channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(title="🔒 Channel locked", description=f"{channel.mention} has been locked.", color=discord.Color.red())
        await ctx.send(embed=embed)

    # ========== MOVEALL ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def moveall(self, ctx, target_channel: discord.VoiceChannel):
        """Moves all members from your voice channel to target channel"""
        if not ctx.author.voice:
            await ctx.send("❌ You are not in a voice channel.")
            return
        
        source_channel = ctx.author.voice.channel
        members = source_channel.members
        count = 0
        
        for member in members:
            await member.move_to(target_channel)
            count += 1
        
        embed = discord.Embed(title="🎤 All members moved", description=f"Moved {count} members from {source_channel.mention} to {target_channel.mention}", color=discord.Color.purple())
        await ctx.send(embed=embed)

    # ========== NICKNAME ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, new_nickname):
        """Changes a member's nickname"""
        old_nick = member.display_name
        await member.edit(nick=new_nickname)
        embed = discord.Embed(title="✏️ Nickname changed", description=f"{member.mention}\nFrom: {old_nick}\nTo: {new_nickname}", color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== PURGE ==========
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Deletes X messages (max 100)"""
        if amount > 100:
            amount = 100
        deleted = await ctx.channel.purge(limit=amount+1)
        msg = await ctx.send(f"🗑️ Deleted {len(deleted)-1} messages")
        await msg.delete(delay=3)

    # ========== ROLE (ADD) ==========
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, role: discord.Role):
        """Adds a role to a member"""
        if role > ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot assign a role above your highest role.")
            return
        await member.add_roles(role)
        embed = discord.Embed(title="✅ Role added", description=f"{member.mention} now has {role.mention}", color=discord.Color.green())
        await ctx.send(embed=embed)

    # ========== REMOVEROLE ==========
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member: discord.Member, role: discord.Role):
        """Removes a role from a member"""
        await member.remove_roles(role)
        embed = discord.Embed(title="✅ Role removed", description=f"{member.mention} lost {role.mention}", color=discord.Color.red())
        await ctx.send(embed=embed)

    # ========== ROLES ==========
    @commands.command()
    async def roles(self, ctx, member: discord.Member = None):
        """Shows all roles of a member"""
        member = member or ctx.author
        role_list = [role.mention for role in member.roles if role != ctx.guild.default_role]
        
        if not role_list:
            await ctx.send(f"{member.mention} has no roles.")
        else:
            embed = discord.Embed(title=f"Roles of {member.display_name}", description="\n".join(role_list), color=discord.Color.blue())
            await ctx.send(embed=embed)

    # ========== SLOWMODE ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int, channel: discord.TextChannel = None):
        """Sets slowmode in seconds (0 to disable)"""
        channel = channel or ctx.channel
        await channel.edit(slowmode_delay=seconds)
        embed = discord.Embed(title="🐌 Slowmode", description=f"Slowmode in {channel.mention} set to {seconds} seconds.", color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== TIMEOUT ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int, *, reason=None):
        """Timeouts a member for X minutes"""
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="⏰ Timed out", description=f"{member.mention} has been timed out for {minutes} minutes.\nReason: {reason}", color=discord.Color.yellow())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Timeout", member, reason)

    # ========== UNBAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name):
        """Unbans a user (Name#1234)"""
        banned_users = [entry async for entry in ctx.guild.bans()]
        for entry in banned_users:
            if str(entry.user) == member_name:
                await ctx.guild.unban(entry.user)
                embed = discord.Embed(title="✅ Unbanned", description=f"{entry.user.mention} has been unbanned.", color=discord.Color.green())
                await ctx.send(embed=embed)
                return
        await ctx.send("❌ User not found.")

    # ========== UNJAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unjail(self, ctx, member: discord.Member):
        """Releases a member from jail"""
        role_name, _ = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if role and role in member.roles:
            await member.remove_roles(role)
            embed = discord.Embed(title="🔓 Released", description=f"{member.mention} has been released from jail.", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {member.mention} is not in jail.")

    # ========== UNLOCK ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlocks a channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(title="🔓 Channel unlocked", description=f"{channel.mention} has been unlocked.", color=discord.Color.green())
        await ctx.send(embed=embed)

    # ========== UNTIMEOUT ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        """Removes timeout from a member"""
        await member.timeout(None)
        embed = discord.Embed(title="🔓 Timeout removed", description=f"{member.mention} is no longer timed out.", color=discord.Color.green())
        await ctx.send(embed=embed)

    # ========== WARN ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warns a member"""
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.add_warn(ctx.guild.id, member.id, reason, str(ctx.author), date)
        
        warn_count = len(self.get_warns(ctx.guild.id, member.id))
        
        embed = discord.Embed(title="⚠️ Warning", description=f"{member.mention} has been warned.\nReason: {reason}\nTotal warnings: {warn_count}", color=discord.Color.orange())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Warning", member, reason)
        
        # Optional: DM to member
        try:
            await member.send(f"📢 You have been warned on **{ctx.guild.name}**.\nReason: {reason}")
        except:
            pass

    # ========== CLEARWARNS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member):
        """Clears all warns of a member"""
        warns_before = len(self.get_warns(ctx.guild.id, member.id))
        self.clear_warns(ctx.guild.id, member.id)
        await ctx.send(f"✅ Cleared {warns_before} warnings from {member.mention}.")

    # ========== WORD FILTER ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wordfilter(self, ctx, action, *, word=None):
        """!wordfilter add <word> | !wordfilter remove <word> | !wordfilter list"""
        if action == "add" and word:
            self.add_wordfilter_word(ctx.guild.id, word)
            await ctx.send(f"✅ `{word}` has been added to the filter list.")
        
        elif action == "remove" and word:
            self.remove_wordfilter_word(ctx.guild.id, word)
            await ctx.send(f"✅ `{word}` has been removed from the filter list.")
        
        elif action == "list":
            words = self.get_wordfilter_words(ctx.guild.id)
            if words:
                await ctx.send(f"📋 **Filtered words:** {', '.join(words)}")
            else:
                await ctx.send("📋 No words are being filtered.")
        
        else:
            await ctx.send("❌ Usage: `!wordfilter add <word>` | `!wordfilter remove <word>` | `!wordfilter list`")

    # ========== WORD FILTER LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        bad_words = self.get_wordfilter_words(message.guild.id)
        content_lower = message.content.lower()
        
        for bad_word in bad_words:
            if bad_word in content_lower:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, that word is not allowed!", delete_after=5)
                break

    # ========== LOG ACTION HELPER ==========
    async def log_action(self, ctx, action, member, reason):
        log_channel_id = self.get_log_channel(ctx.guild.id)
        if log_channel_id:
            channel = ctx.guild.get_channel(int(log_channel_id))
            if channel:
                embed = discord.Embed(title=f"📋 {action}", description=f"**Member:** {member.mention}\n**Reason:** {reason}\n**Mod:** {ctx.author.mention}", color=discord.Color.blue(), timestamp=datetime.now())
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
