import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3

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

    async def check_hierarchy(self, ctx, target):
        """Check if target is above or equal to author/bot"""
        if target == ctx.author:
            await ctx.send(f"❌ **Error:** You cannot perform this action on yourself.")
            return False
        if target.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(f"❌ **Error:** You cannot perform this action on {target.mention} because their role is higher than or equal to yours.")
            return False
        if target.top_role >= ctx.guild.me.top_role:
            await ctx.send(f"❌ **Error:** I cannot perform this action on {target.mention} because their role is higher than or equal to mine.")
            return False
        return True

    async def missing_permission(self, ctx, permission):
        await ctx.send(f"❌ **Missing Permission:** You need `{permission}` to use this command.\n📝 **Example:** `!{ctx.command.name} @user reason`")

    async def missing_member(self, ctx):
        await ctx.send(f"❌ **Wrong Usage:** You need to mention a member.\n📝 **Example:** `!{ctx.command.name} @user reason`")

    # ========== BAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member = None, *, reason="No reason"):
        """Bans a member. Usage: !ban @user reason"""
        if member is None:
            await self.missing_member(ctx)
            return
        if not await self.check_hierarchy(ctx, member):
            return
        await member.ban(reason=reason)
        embed = discord.Embed(title="✅ Banned", description=f"{member.mention} has been banned.\nReason: {reason}", color=discord.Color.red())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Ban", member, reason)

    # ========== CLEARNICK ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def clearnick(self, ctx, member: discord.Member = None):
        """Clears a member's nickname. Usage: !clearnick @user"""
        if member is None:
            await self.missing_member(ctx)
            return
        if not await self.check_hierarchy(ctx, member):
            return
        old_nick = member.display_name
        await member.edit(nick=None)
        embed = discord.Embed(title="🧹 Nickname cleared", description=f"{member.mention}'s nickname has been reset (was: {old_nick})", color=discord.Color.green())
        await ctx.send(embed=embed)

    # ========== DRAG ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def drag(self, ctx, member: discord.Member = None, target_channel: discord.VoiceChannel = None):
        """Drags a member to another voice channel. Usage: !drag @user #voice-channel"""
        if member is None:
            await self.missing_member(ctx)
            return
        if target_channel is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to specify a voice channel.\n📝 **Example:** `!drag @user #General`")
            return
        if not member.voice:
            await ctx.send(f"❌ **Error:** {member.mention} is not in a voice channel.")
            return
        old_channel = member.voice.channel
        await member.move_to(target_channel)
        embed = discord.Embed(title="🎤 Member dragged", description=f"{member.mention} moved from {old_channel.mention} to {target_channel.mention}", color=discord.Color.purple())
        await ctx.send(embed=embed)

    # ========== HISTORY ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def history(self, ctx, member: discord.Member = None, limit: int = 10):
        """Shows warning history of a member. Usage: !history @user [limit]"""
        if member is None:
            await self.missing_member(ctx)
            return
        warns = self.get_warns(ctx.guild.id, member.id)
        if not warns:
            await ctx.send(f"📋 {member.mention} has no warnings.")
            return
        warns = warns[:limit]
        embed = discord.Embed(title=f"⚠️ Warning History of {member.display_name}", color=discord.Color.orange())
        for i, warn in enumerate(warns, 1):
            embed.add_field(name=f"Warning #{i}", value=f"Reason: {warn['reason']}\nBy: {warn['mod']}\nDate: {warn['date']}", inline=False)
        await ctx.send(embed=embed)

    # ========== HISTORYCHANNEL ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def historychannel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel for moderation logs. Usage: !historychannel #channel"""
        if channel:
            self.set_log_channel(ctx.guild.id, channel.id)
            embed = discord.Embed(title="📝 Log channel set", description=f"Moderation logs will be sent to {channel.mention}", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            self.set_log_channel(ctx.guild.id, None)
            await ctx.send("✅ Log channel disabled.")

    # ========== JAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def jail(self, ctx, member: discord.Member = None, *, reason="No reason"):
        """Puts a member in jail. Usage: !jail @user reason"""
        if member is None:
            await self.missing_member(ctx)
            return
        if not await self.check_hierarchy(ctx, member):
            return
        role_name, jail_channel_id = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            role = await ctx.guild.create_role(name=role_name, permissions=discord.Permissions(send_messages=False, add_reactions=False, speak=False))
            await ctx.send(f"⚠️ Role `{role_name}` was automatically created.")
        await member.add_roles(role)
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
            await ctx.send("❌ No jail role found. Use `!jail_settings` to set one up.")
            return
        jailed = [m for m in ctx.guild.members if role in m.roles]
        if not jailed:
            await ctx.send("🔓 No one is in jail.")
        else:
            member_list = "\n".join([f"🔒 {m.mention} - {m.name}" for m in jailed])
            embed = discord.Embed(title="🔒 Jailed Members", description=member_list, color=discord.Color.red())
            await ctx.send(embed=embed)

    # ========== JAIL-SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx, role_name: str = None, channel: discord.TextChannel = None):
        """Sets jail role and jail channel. Usage: !jail_settings @role #channel"""
        if role_name or channel:
            self.set_jail_settings(ctx.guild.id, role_name, channel.id if channel else None)
            await ctx.send(f"✅ Jail settings updated.\nRole: `{role_name or 'unchanged'}`\nChannel: {channel.mention if channel else 'unchanged'}")
        else:
            current_role, current_channel = self.get_jail_settings(ctx.guild.id)
            await ctx.send(f"📋 Current jail settings:\nRole: `{current_role}`\nChannel: {f'<#{current_channel}>' if current_channel else 'Not set'}")

    # ========== KICK ==========
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *, reason="No reason"):
        """Kicks a member. Usage: !kick @user reason"""
        if member is None:
            await self.missing_member(ctx)
            return
        if not await self.check_hierarchy(ctx, member):
            return
        await member.kick(reason=reason)
        embed = discord.Embed(title="✅ Kicked", description=f"{member.mention} has been kicked.\nReason: {reason}", color=discord.Color.orange())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Kick", member, reason)

    # ========== LOCK ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Locks a channel. Usage: !lock #channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(title="🔒 Channel locked", description=f"{channel.mention} has been locked.", color=discord.Color.red())
        await ctx.send(embed=embed)

    # ========== MOVEALL ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def moveall(self, ctx, target_channel: discord.VoiceChannel = None):
        """Moves all members from your voice channel to target channel. Usage: !moveall #voice-channel"""
        if target_channel is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to specify a voice channel.\n📝 **Example:** `!moveall #General`")
            return
        if not ctx.author.voice:
            await ctx.send("❌ **Error:** You are not in a voice channel.")
            return
        source = ctx.author.voice.channel
        members = source.members
        if not members:
            await ctx.send(f"❌ **Error:** No members in {source.mention}")
            return
        count = 0
        for member in members:
            await member.move_to(target_channel)
            count += 1
        embed = discord.Embed(title="🎤 All members moved", description=f"Moved {count} members from {source.mention} to {target_channel.mention}", color=discord.Color.purple())
        await ctx.send(embed=embed)

    # ========== NICKNAME ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member = None, *, new_nickname=None):
        """Changes a member's nickname. Usage: !nickname @user new_nickname"""
        if member is None:
            await self.missing_member(ctx)
            return
        if new_nickname is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to provide a new nickname.\n📝 **Example:** `!nickname @user CoolName`")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        old_nick = member.display_name
        await member.edit(nick=new_nickname)
        embed = discord.Embed(title="✏️ Nickname changed", description=f"{member.mention}\nFrom: `{old_nick}`\nTo: `{new_nickname}`", color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== PURGE ==========
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = None):
        """Deletes X messages (max 100). Usage: !purge 50"""
        if amount is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to specify a number.\n📝 **Example:** `!purge 50`")
            return
        if amount > 100:
            await ctx.send(f"❌ **Error:** You can only purge up to 100 messages at once.")
            return
        if amount < 1:
            await ctx.send(f"❌ **Error:** You need to purge at least 1 message.")
            return
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"🗑️ Deleted {len(deleted)} messages", delete_after=3)

    # ========== ROLE (ADD) ==========
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member = None, role: discord.Role = None):
        """Adds a role to a member. Usage: !role @user @role"""
        if member is None:
            await self.missing_member(ctx)
            return
        if role is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to specify a role.\n📝 **Example:** `!role @user @Member`")
            return
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(f"❌ **Error:** You cannot assign a role above your highest role.")
            return
        await member.add_roles(role)
        embed = discord.Embed(title="✅ Role added", description=f"{member.mention} now has {role.mention}", color=discord.Color.green())
        await ctx.send(embed=embed)

    # ========== REMOVEROLE ==========
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member: discord.Member = None, role: discord.Role = None):
        """Removes a role from a member. Usage: !removerole @user @role"""
        if member is None:
            await self.missing_member(ctx)
            return
        if role is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to specify a role.\n📝 **Example:** `!removerole @user @Member`")
            return
        await member.remove_roles(role)
        embed = discord.Embed(title="✅ Role removed", description=f"{member.mention} lost {role.mention}", color=discord.Color.red())
        await ctx.send(embed=embed)

    # ========== ROLES ==========
    @commands.command()
    async def roles(self, ctx, member: discord.Member = None):
        """Shows all roles of a member. Usage: !roles @user"""
        member = member or ctx.author
        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]
        if not roles:
            await ctx.send(f"📋 {member.mention} has no roles.")
        else:
            embed = discord.Embed(title=f"Roles of {member.display_name}", description=", ".join(roles), color=discord.Color.blue())
            await ctx.send(embed=embed)

    # ========== SLOWMODE ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = None, channel: discord.TextChannel = None):
        """Sets slowmode in seconds (0 to disable). Usage: !slowmode 5 #channel"""
        if seconds is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to specify seconds.\n📝 **Example:** `!slowmode 5`")
            return
        channel = channel or ctx.channel
        await channel.edit(slowmode_delay=seconds)
        embed = discord.Embed(title="🐌 Slowmode", description=f"Slowmode in {channel.mention} set to {seconds} seconds.", color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== TIMEOUT ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member = None, minutes: int = None, *, reason="No reason"):
        """Timeouts a member for X minutes. Usage: !timeout @user 10 reason"""
        if member is None:
            await self.missing_member(ctx)
            return
        if minutes is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to specify minutes.\n📝 **Example:** `!timeout @user 10 Being rude`")
            return
        if not await self.check_hierarchy(ctx, member):
            return
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="⏰ Timed out", description=f"{member.mention} has been timed out for {minutes} minutes.\nReason: {reason}", color=discord.Color.yellow())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Timeout", member, reason)

    # ========== UNBAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name=None):
        """Unbans a user (Name#1234). Usage: !unban Username#1234"""
        if member_name is None:
            await ctx.send(f"❌ **Wrong Usage:** You need to provide the user's name with discriminator.\n📝 **Example:** `!unban CoolUser#1234`")
            return
        banned = [entry async for entry in ctx.guild.bans()]
        for entry in banned:
            if str(entry.user) == member_name:
                await ctx.guild.unban(entry.user)
                embed = discord.Embed(title="✅ Unbanned", description=f"{entry.user.mention} has been unbanned.", color=discord.Color.green())
                await ctx.send(embed=embed)
                return
        await ctx.send(f"❌ User `{member_name}` not found in ban list.")

    # ========== UNJAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unjail(self, ctx, member: discord.Member = None):
        """Releases a member from jail. Usage: !unjail @user"""
        if member is None:
            await self.missing_member(ctx)
            return
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
        """Unlocks a channel. Usage: !unlock #channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(title="🔓 Channel unlocked", description=f"{channel.mention} has been unlocked.", color=discord.Color.green())
        await ctx.send(embed=embed)

    # ========== UNTIMEOUT ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member = None):
        """Removes timeout from a member. Usage: !untimeout @user"""
        if member is None:
            await self.missing_member(ctx)
            return
        await member.timeout(None)
        embed = discord.Embed(title="🔓 Timeout removed", description=f"{member.mention} is no longer timed out.", color=discord.Color.green())
        await ctx.send(embed=embed)

    # ========== WARN ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member = None, *, reason="No reason"):
        """Warns a member. Usage: !warn @user reason"""
        if member is None:
            await self.missing_member(ctx)
            return
        if not await self.check_hierarchy(ctx, member):
            return
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.add_warn(ctx.guild.id, member.id, reason, str(ctx.author), date)
        warn_count = len(self.get_warns(ctx.guild.id, member.id))
        embed = discord.Embed(title="⚠️ Warning", description=f"{member.mention} has been warned.\nReason: {reason}\nTotal warnings: {warn_count}", color=discord.Color.orange())
        await ctx.send(embed=embed)
        await self.log_action(ctx, "Warning", member, reason)

    # ========== CLEARWARNS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member = None):
        """Clears all warns of a member. Usage: !clearwarns @user"""
        if member is None:
            await self.missing_member(ctx)
            return
        count = len(self.get_warns(ctx.guild.id, member.id))
        self.clear_warns(ctx.guild.id, member.id)
        await ctx.send(f"✅ Cleared {count} warnings from {member.mention}.")

    # ========== WORD FILTER ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wordfilter(self, ctx, action=None, *, word=None):
        """!wordfilter add <word> | !wordfilter remove <word> | !wordfilter list"""
        if action is None:
            await ctx.send(f"❌ **Wrong Usage:** `!wordfilter add <word>` | `!wordfilter remove <word>` | `!wordfilter list`")
            return
        if action == "add" and word:
            self.add_wordfilter_word(ctx.guild.id, word)
            await ctx.send(f"✅ `{word}` added to filter list.")
        elif action == "remove" and word:
            self.remove_wordfilter_word(ctx.guild.id, word)
            await ctx.send(f"✅ `{word}` removed from filter list.")
        elif action == "list":
            words = self.get_wordfilter_words(ctx.guild.id)
            if words:
                await ctx.send(f"📋 **Filtered words:** {', '.join(words)}")
            else:
                await ctx.send("📋 No words are being filtered.")
        else:
            await ctx.send(f"❌ **Wrong Usage:** `!wordfilter add <word>` | `!wordfilter remove <word>` | `!wordfilter list`")

    # ========== WORD FILTER LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        bad_words = self.get_wordfilter_words(message.guild.id)
        for word in bad_words:
            if word in message.content.lower():
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, that word is not allowed!", delete_after=3)
                break

    # ========== ERROR HANDLER ==========
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing = error.missing_permissions[0] if error.missing_permissions else "unknown"
            await ctx.send(f"❌ **Missing Permission:** You need `{missing}` to use `!{ctx.command.name}`.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(f"❌ **Member not found.** Please mention a valid member.\n📝 **Example:** `!{ctx.command.name} @user`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ **Invalid argument.**\n📝 **Example:** `!{ctx.command.name} @user reason`")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ **Missing argument.**\n📝 **Example:** `!{ctx.command.name} @user reason`")
        else:
            print(f"Unhandled error: {error}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
