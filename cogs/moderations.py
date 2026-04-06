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
        print("✅ Moderation Cog geladen")

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

    # ========== HELPER ==========
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

    async def error_embed(self, ctx, title, desc, example=None):
        embed = discord.Embed(title=f"❌ {title}", description=desc, color=discord.Color.red())
        if example:
            embed.add_field(name="📝 Example", value=f"`{example}`", inline=False)
        await ctx.send(embed=embed)

    async def success_embed(self, ctx, title, desc, color=discord.Color.green()):
        embed = discord.Embed(title=f"✅ {title}", description=desc, color=color)
        await ctx.send(embed=embed)

    async def check_hierarchy(self, ctx, target):
        if target == ctx.author:
            await self.error_embed(ctx, "Action Failed", "You cannot perform this action on yourself.")
            return False
        if target.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await self.error_embed(ctx, "Hierarchy Error", f"You cannot perform this action on {target.mention} because their role is higher than or equal to yours.")
            return False
        if target.top_role >= ctx.guild.me.top_role:
            await self.error_embed(ctx, "Bot Hierarchy Error", f"I cannot perform this action on {target.mention} because their role is higher than or equal to mine.")
            return False
        return True

    # ========== BAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason"):
        """Bans a member"""
        if not await self.check_hierarchy(ctx, member):
            return
        await member.ban(reason=reason)
        await self.success_embed(ctx, "Member Banned", f"{member.mention} has been banned.\n**Reason:** {reason}", discord.Color.red())

    # ========== CLEARNICK ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def clearnick(self, ctx, member: discord.Member):
        """Clears a member's nickname"""
        if not await self.check_hierarchy(ctx, member):
            return
        old = member.display_name
        await member.edit(nick=None)
        await self.success_embed(ctx, "Nickname Cleared", f"{member.mention}'s nickname has been reset.\n**Was:** `{old}`")

    # ========== DRAG ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def drag(self, ctx, member: discord.Member, target: discord.VoiceChannel):
        """Drags a member to another voice channel"""
        if not member.voice:
            await self.error_embed(ctx, "Not in Voice", f"{member.mention} is not in a voice channel.")
            return
        old = member.voice.channel
        await member.move_to(target)
        await self.success_embed(ctx, "Member Dragged", f"{member.mention} moved from {old.mention} to {target.mention}", discord.Color.purple())

    # ========== HISTORY ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def history(self, ctx, member: discord.Member, limit: int = 10):
        """Shows warning history of a member"""
        warns = self.get_warns(ctx.guild.id, member.id)
        if not warns:
            await self.error_embed(ctx, "No Warnings", f"{member.mention} has no warnings.")
            return
        warns = warns[:limit]
        embed = discord.Embed(title=f"⚠️ Warning History of {member.display_name}", color=discord.Color.orange())
        for i, w in enumerate(warns, 1):
            embed.add_field(name=f"Warning #{i}", value=f"**Reason:** {w['reason']}\n**By:** {w['mod']}\n**Date:** {w['date']}", inline=False)
        await ctx.send(embed=embed)

    # ========== HISTORYCHANNEL ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def historychannel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel for moderation logs"""
        if channel:
            self.set_log_channel(ctx.guild.id, str(channel.id))
            await self.success_embed(ctx, "Log Channel Set", f"Moderation logs will be sent to {channel.mention}")
        else:
            self.set_log_channel(ctx.guild.id, None)
            await self.success_embed(ctx, "Log Channel Disabled", "Moderation logs have been disabled.")

    # ========== JAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def jail(self, ctx, member: discord.Member, *, reason="No reason"):
        """Puts a member in jail"""
        if not await self.check_hierarchy(ctx, member):
            return
        role_name, jail_channel_id = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            role = await ctx.guild.create_role(name=role_name, permissions=discord.Permissions(send_messages=False, add_reactions=False, speak=False))
        await member.add_roles(role)
        await self.success_embed(ctx, "Member Jailed", f"{member.mention} has been put in jail.\n**Reason:** {reason}", discord.Color.red())

    # ========== JAIL-LIST ==========
    @commands.command()
    async def jail_list(self, ctx):
        """Shows all jailed members"""
        role_name, _ = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await self.error_embed(ctx, "No Jail Role", "No jail role found. Use `!jail_settings` to set one up.")
            return
        jailed = [m for m in ctx.guild.members if role in m.roles]
        if not jailed:
            await self.error_embed(ctx, "No Jailed Members", "No one is currently in jail.")
        else:
            embed = discord.Embed(title="🔒 Jailed Members", description="\n".join([f"• {m.mention}" for m in jailed]), color=discord.Color.red())
            await ctx.send(embed=embed)

    # ========== JAIL-SETTINGS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx, role_name: str = None, channel: discord.TextChannel = None):
        """Sets jail role and jail channel"""
        if role_name or channel:
            self.set_jail_settings(ctx.guild.id, role_name, str(channel.id) if channel else None)
            await self.success_embed(ctx, "Jail Settings Updated", f"**Role:** `{role_name or 'unchanged'}`\n**Channel:** {channel.mention if channel else 'unchanged'}")
        else:
            current_role, current_channel = self.get_jail_settings(ctx.guild.id)
            embed = discord.Embed(title="⚙️ Current Jail Settings", color=discord.Color.blue())
            embed.add_field(name="Role", value=f"`{current_role}`", inline=True)
            embed.add_field(name="Channel", value=f"<#{current_channel}>" if current_channel else "Not set", inline=True)
            await ctx.send(embed=embed)

    # ========== KICK ==========
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason"):
        """Kicks a member"""
        if not await self.check_hierarchy(ctx, member):
            return
        await member.kick(reason=reason)
        await self.success_embed(ctx, "Member Kicked", f"{member.mention} has been kicked.\n**Reason:** {reason}", discord.Color.orange())

    # ========== LOCK ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Locks a channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await self.success_embed(ctx, "Channel Locked", f"{channel.mention} has been locked.", discord.Color.red())

    # ========== MOVEALL ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def moveall(self, ctx, target: discord.VoiceChannel):
        """Moves all members from your voice channel to target channel"""
        if not ctx.author.voice:
            await self.error_embed(ctx, "Not in Voice", "You are not in a voice channel.")
            return
        source = ctx.author.voice.channel
        members = source.members
        if not members:
            await self.error_embed(ctx, "No Members", f"No members in {source.mention} to move.")
            return
        count = 0
        for m in members:
            await m.move_to(target)
            count += 1
        await self.success_embed(ctx, "All Members Moved", f"Moved **{count}** members from {source.mention} to {target.mention}", discord.Color.purple())

    # ========== NICKNAME ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, new_nickname: str):
        """Changes a member's nickname"""
        if not await self.check_hierarchy(ctx, member):
            return
        old = member.display_name
        await member.edit(nick=new_nickname)
        await self.success_embed(ctx, "Nickname Changed", f"{member.mention}\n**From:** `{old}`\n**To:** `{new_nickname}`")

    # ========== PURGE ==========
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Deletes X messages (max 100)"""
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
    async def role(self, ctx, member: discord.Member, role: discord.Role):
        """Adds a role to a member. Alias: !r"""
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await self.error_embed(ctx, "Role Hierarchy Error", "You cannot assign a role above your highest role.")
            return
        await member.add_roles(role)
        await self.success_embed(ctx, "Role Added", f"{member.mention} now has {role.mention}")

    # ========== REMOVEROLE ==========
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member: discord.Member, role: discord.Role):
        """Removes a role from a member"""
        await member.remove_roles(role)
        await self.success_embed(ctx, "Role Removed", f"{member.mention} lost {role.mention}", discord.Color.red())

    # ========== ROLES ==========
    @commands.command()
    async def roles(self, ctx, member: discord.Member = None):
        """Shows all roles of a member"""
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
    async def slowmode(self, ctx, seconds: int, channel: discord.TextChannel = None):
        """Sets slowmode in seconds (0 to disable)"""
        channel = channel or ctx.channel
        await channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await self.success_embed(ctx, "Slowmode Disabled", f"Slowmode in {channel.mention} has been disabled.")
        else:
            await self.success_embed(ctx, "Slowmode Set", f"Slowmode in {channel.mention} set to **{seconds}** seconds.")

    # ========== TIMEOUT ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int, *, reason="No reason"):
        """Timeouts a member for X minutes"""
        if not await self.check_hierarchy(ctx, member):
            return
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await self.success_embed(ctx, "Member Timed Out", f"{member.mention} has been timed out for **{minutes}** minutes.\n**Reason:** {reason}", discord.Color.yellow())

    # ========== UNBAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name: str):
        """Unbans a user (Name#1234)"""
        banned = [entry async for entry in ctx.guild.bans()]
        for entry in banned:
            if str(entry.user) == member_name:
                await ctx.guild.unban(entry.user)
                await self.success_embed(ctx, "Member Unbanned", f"{entry.user.mention} has been unbanned.")
                return
        await self.error_embed(ctx, "Member Not Found", f"User `{member_name}` not found in ban list.", "unban Username#1234")

    # ========== UNJAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unjail(self, ctx, member: discord.Member):
        """Releases a member from jail"""
        role_name, _ = self.get_jail_settings(ctx.guild.id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role and role in member.roles:
            await member.remove_roles(role)
            await self.success_embed(ctx, "Member Released", f"{member.mention} has been released from jail.")
        else:
            await self.error_embed(ctx, "Not in Jail", f"{member.mention} is not in jail.")

    # ========== UNLOCK ==========
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlocks a channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await self.success_embed(ctx, "Channel Unlocked", f"{channel.mention} has been unlocked.")

    # ========== UNTIMEOUT ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        """Removes timeout from a member"""
        await member.timeout(None)
        await self.success_embed(ctx, "Timeout Removed", f"{member.mention} is no longer timed out.")

    # ========== WARN ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason"):
        """Warns a member"""
        if not await self.check_hierarchy(ctx, member):
            return
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.add_warn(ctx.guild.id, member.id, reason, str(ctx.author), date)
        count = len(self.get_warns(ctx.guild.id, member.id))
        await self.success_embed(ctx, "Member Warned", f"{member.mention} has been warned.\n**Reason:** {reason}\n**Total warnings:** {count}", discord.Color.orange())

    # ========== CLEARWARNS ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member):
        """Clears all warns of a member"""
        count = len(self.get_warns(ctx.guild.id, member.id))
        self.clear_warns(ctx.guild.id, member.id)
        await self.success_embed(ctx, "Warnings Cleared", f"Cleared **{count}** warnings from {member.mention}.")

    # ========== WORD FILTER ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wordfilter(self, ctx, action: str, *, word: str = None):
        """!wordfilter add <word> | !wordfilter remove <word> | !wordfilter list"""
        if action == "add" and word:
            self.add_wordfilter_word(ctx.guild.id, word)
            await self.success_embed(ctx, "Word Added", f"`{word}` added to filter list.")
        elif action == "remove" and word:
            self.remove_wordfilter_word(ctx.guild.id, word)
            await self.success_embed(ctx, "Word Removed", f"`{word}` removed from filter list.")
        elif action == "list":
            words = self.get_wordfilter_words(ctx.guild.id)
            if words:
                embed = discord.Embed(title="📋 Filtered Words", description=", ".join([f"`{w}`" for w in words]), color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await self.error_embed(ctx, "No Words", "No words are currently being filtered.", "wordfilter add badword")
        else:
            await self.error_embed(ctx, "Invalid Usage", "Use: `add`, `remove`, or `list`", "wordfilter add badword")

    # ========== WORD FILTER LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        words = self.get_wordfilter_words(message.guild.id)
        for word in words:
            if word in message.content.lower():
                await message.delete()
                embed = discord.Embed(title="⚠️ Filtered Message", description=f"{message.author.mention}, that word is not allowed!", color=discord.Color.red())
                await message.channel.send(embed=embed, delete_after=3)
                break

    # ========== ERROR HANDLER ==========
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.error_embed(ctx, "Missing Permission", f"You need `{error.missing_permissions[0]}` to use this command.")
        elif isinstance(error, commands.MemberNotFound):
            await self.error_embed(ctx, "Member Not Found", "Please mention a valid member.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await self.error_embed(ctx, "Missing Argument", "You are missing a required argument.", f"{ctx.command.name} @user reason")
        else:
            print(f"Error: {error}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
