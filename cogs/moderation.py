import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3
import re

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "moderation.db"
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            reason TEXT,
            mod_name TEXT,
            date TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS jail_settings (
            guild_id TEXT PRIMARY KEY,
            role_name TEXT,
            channel_id TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS log_settings (
            guild_id TEXT PRIMARY KEY,
            channel_id TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS wordfilters (
            guild_id TEXT,
            word TEXT,
            PRIMARY KEY (guild_id, word)
        )''')
        conn.commit()
        conn.close()

    def get_warns(self, guild_id, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT reason, mod_name, date FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY id DESC", (str(guild_id), str(user_id)))
        result = c.fetchall()
        conn.close()
        return [{"reason": r[0], "mod": r[1], "date": r[2]} for r in result]

    def add_warn(self, guild_id, user_id, reason, mod_name, date):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO warns (guild_id, user_id, reason, mod_name, date) VALUES (?, ?, ?, ?, ?)",
                  (str(guild_id), str(user_id), reason, mod_name, date))
        conn.commit()
        conn.close()

    def clear_warns(self, guild_id, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM warns WHERE guild_id = ? AND user_id = ?", (str(guild_id), str(user_id)))
        conn.commit()
        conn.close()

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

    async def log_action(self, ctx, action, member, reason):
        log_channel_id = self.get_log_channel(ctx.guild.id)
        if log_channel_id:
            channel = ctx.guild.get_channel(int(log_channel_id))
            if channel:
                embed = discord.Embed(title=f"📋 {action}", description=f"**Member:** {member.mention}\n**Reason:** {reason}\n**Mod:** {ctx.author.mention}", color=discord.Color.blue(), timestamp=datetime.now())
                await channel.send(embed=embed)

    async def error_embed(self, ctx, title, description, example=None):
        embed = discord.Embed(title=f"❌ {title}", description=description, color=discord.Color.red())
        if example:
            embed.add_field(name="📝 Example", value=f"`{example}`", inline=False)
        await ctx.send(embed=embed)

    async def success_embed(self, ctx, title, description, color=discord.Color.green()):
        embed = discord.Embed(title=f"✅ {title}", description=description, color=color)
        await ctx.send(embed=embed)

    async def check_hierarchy(self, ctx, target):
        if target == ctx.author:
            await self.error_embed(ctx, "Action Failed", f"You cannot perform this action on yourself.", f"{ctx.command.name} @user reason")
            return False
        if target.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await self.error_embed(ctx, "Hierarchy Error", f"You cannot perform this action on {target.mention} because their role is higher than or equal to yours.", f"{ctx.command.name} @user reason")
            return False
        if target.top_role >= ctx.guild.me.top_role:
            await self.error_embed(ctx, "Bot Hierarchy Error", f"I cannot perform this action on {target.mention} because their role is higher than or equal to mine.", f"{ctx.command.name} @user reason")
            return False
        return True

    def parse_time(self, time_str):
        """Parses time strings like 10m, 30s, 2h, 1d into seconds"""
        match = re.match(r'(\d+)([smhd])', time_str.lower())
        if not match:
            return None
        value = int(match.group(1))
        unit = match.group(2)
        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        return None

    # ========== BAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member = None, *, reason="No reason"):
        """Bans a member"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to ban.", "ban @user spamming")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        await member.ban(reason=reason)
        await self.success_embed(ctx, "Member Banned", f"{member.mention} has been banned.\n**Reason:** {reason}", discord.Color.red())
        await self.log_action(ctx, "Ban", member, reason)

    # ========== CLEARNICK ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def clearnick(self, ctx, member: discord.Member = None):
        """Clears a member's nickname"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to clear their nickname.", "clearnick @user")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        old_nick = member.display_name
        await member.edit(nick=None)
        await self.success_embed(ctx, "Nickname Cleared", f"{member.mention}'s nickname has been reset.\n**Was:** `{old_nick}`", discord.Color.blue())

    # ========== DRAG ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def drag(self, ctx, member: discord.Member = None, target_channel: discord.VoiceChannel = None):
        """Drags a member to another voice channel"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to drag.", "drag @user #General")
            return
        if target_channel is None:
            await self.error_embed(ctx, "Missing Channel", "You need to specify a voice channel.", "drag @user #General")
            return
        if not member.voice:
            await self.error_embed(ctx, "Not in Voice", f"{member.mention} is not in a voice channel.", "drag @user #General")
            return
        old_channel = member.voice.channel
        await member.move_to(target_channel)
        await self.success_embed(ctx, "Member Dragged", f"{member.mention} moved from {old_channel.mention} to {target_channel.mention}", discord.Color.purple())

    # ========== HISTORY ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def history(self, ctx, member: discord.Member = None, limit: int = 10):
        """Shows warning history of a member"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to see their warning history.", "history @user")
            return
        warns = self.get_warns(ctx.guild.id, member.id)
        if not warns:
            await self.error_embed(ctx, "No Warnings", f"{member.mention} has no warnings.", "history @user")
            return
        warns = warns[:limit]
        embed = discord.Embed(title=f"⚠️ Warning History of {member.display_name}", color=discord.Color.orange())
        for i, warn in enumerate(warns, 1):
            embed.add_field(name=f"Warning #{i}", value=f"**Reason:** {warn['reason']}\n**By:** {warn['mod']}\n**Date:** {warn['date']}", inline=False)
        await ctx.send(embed=embed)

    # ========== HISTORYCHANNEL ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def historychannel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel for moderation logs"""
        if channel:
            self.set_log_channel(ctx.guild.id, channel.id)
            await self.success_embed(ctx, "Log Channel Set", f"Moderation logs will be sent to {channel.mention}", discord.Color.green())
        else:
            self.set_log_channel(ctx.guild.id, None)
            await self.success_embed(ctx, "Log Channel Disabled", "Moderation logs have been disabled.", discord.Color.gray())

    # ========== JAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def jail(self, ctx, member: discord.Member = None, *, reason="No reason"):
        """Puts a member in jail"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to jail.", "jail @user spamming")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        role_name, jail_channel_id = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            role = await ctx.guild.create_role(name=role_name, permissions=discord.Permissions(send_messages=False, add_reactions=False, speak=False))
            await ctx.send(f"⚠️ Role `{role_name}` was automatically created.")
        await member.add_roles(role)
        await self.success_embed(ctx, "Member Jailed", f"{member.mention} has been put in jail.\n**Reason:** {reason}", discord.Color.red())
        await self.log_action(ctx, "Jail", member, reason)

    # ========== JAIL-LIST ==========
    @commands.command()
    async def jail_list(self, ctx):
        """Shows all jailed members"""
        role_name, _ = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await self.error_embed(ctx, "No Jail Role", "No jail role found. Use `!jail_settings` to set one up.", "jail_settings @Jailed #jail-channel")
            return
        jailed = [m for m in ctx.guild.members if role in m.roles]
        if not jailed:
            await self.error_embed(ctx, "No Jailed Members", "No one is currently in jail.", "jail_list")
        else:
            member_list = "\n".join([f"🔒 {m.mention} - {m.name}" for m in jailed])
            embed = discord.Embed(title="🔒 Jailed Members", description=member_list, color=discord.Color.red())
            await ctx.send(embed=embed)

    # ========== JAIL-SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx, role_name: str = None, channel: discord.TextChannel = None):
        """Sets jail role and jail channel"""
        if role_name or channel:
            self.set_jail_settings(ctx.guild.id, role_name, channel.id if channel else None)
            await self.success_embed(ctx, "Jail Settings Updated", f"**Role:** `{role_name or 'unchanged'}`\n**Channel:** {channel.mention if channel else 'unchanged'}", discord.Color.green())
        else:
            current_role, current_channel = self.get_jail_settings(ctx.guild.id)
            embed = discord.Embed(title="⚙️ Current Jail Settings", color=discord.Color.blue())
            embed.add_field(name="Role", value=f"`{current_role}`", inline=True)
            embed.add_field(name="Channel", value=f"<#{current_channel}>" if current_channel else "Not set", inline=True)
            await ctx.send(embed=embed)

    # ========== KICK ==========
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *, reason="No reason"):
        """Kicks a member"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to kick.", "kick @user spamming")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        await member.kick(reason=reason)
        await self.success_embed(ctx, "Member Kicked", f"{member.mention} has been kicked.\n**Reason:** {reason}", discord.Color.orange())
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
        await self.success_embed(ctx, "Channel Locked", f"{channel.mention} has been locked. Members cannot send messages.", discord.Color.red())

    # ========== MOVEALL ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def moveall(self, ctx, target_channel: discord.VoiceChannel = None):
        """Moves all members from your voice channel to target channel"""
        if target_channel is None:
            await self.error_embed(ctx, "Missing Channel", "You need to specify a voice channel.", "moveall #General")
            return
        if not ctx.author.voice:
            await self.error_embed(ctx, "Not in Voice", "You are not in a voice channel.", "moveall #General")
            return
        source = ctx.author.voice.channel
        members = source.members
        if not members:
            await self.error_embed(ctx, "No Members", f"No members in {source.mention} to move.", "moveall #General")
            return
        count = 0
        for member in members:
            await member.move_to(target_channel)
            count += 1
        await self.success_embed(ctx, "All Members Moved", f"Moved **{count}** members from {source.mention} to {target_channel.mention}", discord.Color.purple())

    # ========== NICKNAME ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member = None, *, new_nickname=None):
        """Changes a member's nickname"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to change their nickname.", "nickname @user CoolName")
            return
        if new_nickname is None:
            await self.error_embed(ctx, "Missing Nickname", "You need to provide a new nickname.", "nickname @user CoolName")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        old_nick = member.display_name
        await member.edit(nick=new_nickname)
        await self.success_embed(ctx, "Nickname Changed", f"{member.mention}\n**From:** `{old_nick}`\n**To:** `{new_nickname}`", discord.Color.blue())

    # ========== PURGE ==========
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = None):
        """Deletes X messages (max 100)"""
        if amount is None:
            await self.error_embed(ctx, "Missing Amount", "You need to specify how many messages to delete.", "purge 50")
            return
        if amount > 100:
            await self.error_embed(ctx, "Too Many Messages", "You can only purge up to 100 messages at once.", "purge 50")
            return
        if amount < 1:
            await self.error_embed(ctx, "Invalid Amount", "You need to purge at least 1 message.", "purge 50")
            return
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"🗑️ Deleted **{len(deleted)}** messages", delete_after=3)

    # ========== ROLE (ADD) ==========
    @commands.command(aliases=["r"])
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member = None, role: discord.Role = None):
        """Adds a role to a member. Alias: !r"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to add a role.", "role @user @Member or r @user @Member")
            return
        if role is None:
            await self.error_embed(ctx, "Missing Role", "You need to specify a role to add.", "role @user @Member or r @user @Member")
            return
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await self.error_embed(ctx, "Role Hierarchy Error", "You cannot assign a role above your highest role.", "role @user @Member")
            return
        await member.add_roles(role)
        await self.success_embed(ctx, "Role Added", f"{member.mention} now has {role.mention}", discord.Color.green())

    # ========== REMOVEROLE ==========
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member: discord.Member = None, role: discord.Role = None):
        """Removes a role from a member"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to remove a role.", "removerole @user @Member")
            return
        if role is None:
            await self.error_embed(ctx, "Missing Role", "You need to specify a role to remove.", "removerole @user @Member")
            return
        await member.remove_roles(role)
        await self.success_embed(ctx, "Role Removed", f"{member.mention} lost {role.mention}", discord.Color.red())

    # ========== ROLES ==========
    @commands.command()
    async def roles(self, ctx, member: discord.Member = None):
        """Shows all roles of a member"""
        member = member or ctx.author
        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]
        if not roles:
            embed = discord.Embed(title=f"📋 Roles of {member.display_name}", description="No roles", color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=f"📋 Roles of {member.display_name}", description=", ".join(roles), color=discord.Color.blue())
            await ctx.send(embed=embed)

    # ========== SLOWMODE ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = None, channel: discord.TextChannel = None):
        """Sets slowmode in seconds (0 to disable)"""
        if seconds is None:
            await self.error_embed(ctx, "Missing Seconds", "You need to specify the slowmode duration in seconds.", "slowmode 5")
            return
        channel = channel or ctx.channel
        await channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await self.success_embed(ctx, "Slowmode Disabled", f"Slowmode in {channel.mention} has been disabled.", discord.Color.green())
        else:
            await self.success_embed(ctx, "Slowmode Set", f"Slowmode in {channel.mention} set to **{seconds}** seconds.", discord.Color.blue())

    # ========== TIMEOUT ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member = None, duration: str = None, *, reason="No reason"):
        """Timeouts a member. Duration: 30s, 10m, 2h, 1d"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to timeout.", "timeout @user 10m being rude")
            return
        if duration is None:
            await self.error_embed(ctx, "Missing Duration", "You need to specify the timeout duration.\n**Formats:** `30s`, `10m`, `2h`, `1d`", "timeout @user 10m being rude")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        
        seconds = self.parse_time(duration)
        if seconds is None:
            await self.error_embed(ctx, "Invalid Duration", "Invalid time format.\n**Formats:** `30s`, `10m`, `2h`, `1d`", "timeout @user 10m being rude")
            return
        
        if seconds < 1:
            await self.error_embed(ctx, "Invalid Duration", "Duration must be at least 1 second.", "timeout @user 10m")
            return
        if seconds > 2419200:  # 28 days max
            await self.error_embed(ctx, "Duration Too Long", "Timeout cannot be longer than 28 days.", "timeout @user 10m")
            return
        
        duration_obj = timedelta(seconds=seconds)
        await member.timeout(duration_obj, reason=reason)
        
        # Format duration for display
        if seconds < 60:
            display = f"{seconds} seconds"
        elif seconds < 3600:
            display = f"{seconds // 60} minutes"
        elif seconds < 86400:
            display = f"{seconds // 3600} hours"
        else:
            display = f"{seconds // 86400} days"
        
        await self.success_embed(ctx, "Member Timed Out", f"{member.mention} has been timed out for **{display}**.\n**Reason:** {reason}", discord.Color.yellow())
        await self.log_action(ctx, "Timeout", member, reason)

    # ========== UNBAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name=None):
        """Unbans a user (Name#1234)"""
        if member_name is None:
            await self.error_embed(ctx, "Missing Member", "You need to provide the user's name with discriminator.", "unban CoolUser#1234")
            return
        banned = [entry async for entry in ctx.guild.bans()]
        for entry in banned:
            if str(entry.user) == member_name:
                await ctx.guild.unban(entry.user)
                await self.success_embed(ctx, "Member Unbanned", f"{entry.user.mention} has been unbanned.", discord.Color.green())
                return
        await self.error_embed(ctx, "Member Not Found", f"User `{member_name}` not found in ban list.", "unban CoolUser#1234")

    # ========== UNJAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unjail(self, ctx, member: discord.Member = None):
        """Releases a member from jail"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to unjail.", "unjail @user")
            return
        role_name, _ = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role and role in member.roles:
            await member.remove_roles(role)
            await self.success_embed(ctx, "Member Released", f"{member.mention} has been released from jail.", discord.Color.green())
        else:
            await self.error_embed(ctx, "Not in Jail", f"{member.mention} is not in jail.", "unjail @user")

    # ========== UNLOCK ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlocks a channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await self.success_embed(ctx, "Channel Unlocked", f"{channel.mention} has been unlocked. Members can now send messages.", discord.Color.green())

    # ========== UNTIMEOUT ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member = None):
        """Removes timeout from a member"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to remove timeout.", "untimeout @user")
            return
        await member.timeout(None)
        await self.success_embed(ctx, "Timeout Removed", f"{member.mention} is no longer timed out.", discord.Color.green())

    # ========== WARN ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member = None, *, reason="No reason"):
        """Warns a member"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to warn.", "warn @user spamming")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.add_warn(ctx.guild.id, member.id, reason, str(ctx.author), date)
        warn_count = len(self.get_warns(ctx.guild.id, member.id))
        await self.success_embed(ctx, "Member Warned", f"{member.mention} has been warned.\n**Reason:** {reason}\n**Total warnings:** {warn_count}", discord.Color.orange())
        await self.log_action(ctx, "Warning", member, reason)

    # ========== CLEARWARNS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member = None):
        """Clears all warns of a member"""
        if member is None:
            await self.error_embed(ctx, "Missing Member", "You need to mention a member to clear warnings.", "clearwarns @user")
            return
        count = len(self.get_warns(ctx.guild.id, member.id))
        self.clear_warns(ctx.guild.id, member.id)
        await self.success_embed(ctx, "Warnings Cleared", f"Cleared **{count}** warnings from {member.mention}.", discord.Color.green())

    # ========== WORD FILTER ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wordfilter(self, ctx, action=None, *, word=None):
        """!wordfilter add <word> | !wordfilter remove <word> | !wordfilter list"""
        if action is None:
            embed = discord.Embed(title="📋 Wordfilter Usage", color=discord.Color.blue())
            embed.add_field(name="Add word", value="`!wordfilter add badword`", inline=False)
            embed.add_field(name="Remove word", value="`!wordfilter remove badword`", inline=False)
            embed.add_field(name="List words", value="`!wordfilter list`", inline=False)
            await ctx.send(embed=embed)
            return
        if action == "add" and word:
            self.add_wordfilter_word(ctx.guild.id, word)
            await self.success_embed(ctx, "Word Added", f"`{word}` has been added to the filter list.", discord.Color.green())
        elif action == "remove" and word:
            self.remove_wordfilter_word(ctx.guild.id, word)
            await self.success_embed(ctx, "Word Removed", f"`{word}` has been removed from the filter list.", discord.Color.green())
        elif action == "list":
            words = self.get_wordfilter_words(ctx.guild.id)
            if words:
                embed = discord.Embed(title="📋 Filtered Words", description=", ".join([f"`{w}`" for w in words]), color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await self.error_embed(ctx, "No Words", "No words are currently being filtered.", "wordfilter add badword")

    # ========== WORD FILTER LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        bad_words = self.get_wordfilter_words(message.guild.id)
        for word in bad_words:
            if word in message.content.lower():
                await message.delete()
                embed = discord.Embed(title="⚠️ Filtered Message", description=f"{message.author.mention}, that word is not allowed!", color=discord.Color.red())
                await message.channel.send(embed=embed, delete_after=3)
                break

    # ========== ERROR HANDLER ==========
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing = error.missing_permissions[0] if error.missing_permissions else "unknown"
            embed = discord.Embed(title="❌ Missing Permission", description=f"You need `{missing}` to use `!{ctx.command.name}`.", color=discord.Color.red())
            embed.add_field(name="📝 Example", value=f"`!{ctx.command.name} @user reason`", inline=False)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="❌ Member Not Found", description="Please mention a valid member.", color=discord.Color.red())
            embed.add_field(name="📝 Example", value=f"`!{ctx.command.name} @user reason`", inline=False)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="❌ Invalid Argument", description="Please check your command arguments.", color=discord.Color.red())
            embed.add_field(name="📝 Example", value=f"`!{ctx.command.name} @user reason`", inline=False)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="❌ Missing Argument", description="You are missing a required argument.", color=discord.Color.red())
            embed.add_field(name="📝 Example", value=f"`!{ctx.command.name} @user reason`", inline=False)
            await ctx.send(embed=embed)
        else:
            print(f"Unhandled error: {error}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
