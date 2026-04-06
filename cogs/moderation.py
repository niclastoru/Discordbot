import discord
from discord.ext import commands
from datetime import datetime, timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warns = {}  # {member_id: [{"reason": "", "mod": "", "date": ""}]}
        self.bad_words = []  # List of filtered words
        self.jailed_role_name = "Jailed"
        self.jail_channel_id = None
        self.log_channel_id = None

    # ========== BAN ==========
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Bans a member"""
        await member.ban(reason=reason)
        embed = discord.Embed(title="✅ Banned", description=f"{member.mention} has been banned.\nReason: {reason}", color=discord.Color.red())
        await ctx.send(embed=embed)

    # ========== CLEARNICK ==========
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def clearnick(self, ctx, member: discord.Member):
        """Clears a member's nickname"""
        await member.edit(nick=None)
        embed = discord.Embed(title="🧹 Nickname cleared", description=f"{member.mention}'s nickname has been reset to {member.name}", color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== DRAG ==========
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def drag(self, ctx, member: discord.Member, target_channel: discord.VoiceChannel):
        """Drags a member to another voice channel"""
        if member.voice and member.voice.channel:
            await member.move_to(target_channel)
            embed = discord.Embed(title="🎤 Member moved", description=f"{member.mention} has been moved to {target_channel.mention}", color=discord.Color.purple())
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Member is not in a voice channel.")

    # ========== HISTORY ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def history(self, ctx, member: discord.Member, limit: int = 10):
        """Shows warning history of a member"""
        if member.id not in self.warns or not self.warns[member.id]:
            await ctx.send(f"{member.mention} has no warnings.")
            return
        
        warns = self.warns[member.id][-limit:]
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
            self.log_channel_id = channel.id
            embed = discord.Embed(title="📝 Log channel set", description=f"History will be logged in {channel.mention}", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Please specify a channel: `!historychannel #channel`")

    # ========== JAIL ==========
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def jail(self, ctx, member: discord.Member, *, reason=None):
        """Puts a member in jail"""
        role = discord.utils.get(ctx.guild.roles, name=self.jailed_role_name)
        if not role:
            role = await ctx.guild.create_role(name=self.jailed_role_name, permissions=discord.Permissions(send_messages=False, add_reactions=False))
            await ctx.send(f"⚠️ Role `{self.jailed_role_name}` was automatically created.")
        
        await member.add_roles(role)
        
        if self.jail_channel_id:
            jail_channel = ctx.guild.get_channel(self.jail_channel_id)
            if jail_channel:
                await jail_channel.send(f"{member.mention} has been jailed. Reason: {reason}")
        
        embed = discord.Embed(title="🔒 Jailed", description=f"{member.mention} has been put in jail.\nReason: {reason}", color=discord.Color.red())
        await ctx.send(embed=embed)

    # ========== JAIL-LIST ==========
    @commands.command()
    async def jail_list(self, ctx):
        """Shows all jailed members"""
        role = discord.utils.get(ctx.guild.roles, name=self.jailed_role_name)
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
        if role_name:
            self.jailed_role_name = role_name
            await ctx.send(f"✅ Jail role set to `{role_name}`.")
        if channel:
            self.jail_channel_id = channel.id
            await ctx.send(f"✅ Jail channel set to {channel.mention}.")

    # ========== KICK ==========
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kicks a member"""
        await member.kick(reason=reason)
        embed = discord.Embed(title="✅ Kicked", description=f"{member.mention} has been kicked.\nReason: {reason}", color=discord.Color.orange())
        await ctx.send(embed=embed)

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

    # ========== ROLE (REMOVE) ==========
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
        role = discord.utils.get(ctx.guild.roles, name=self.jailed_role_name)
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
        if member.id not in self.warns:
            self.warns[member.id] = []
        
        warn_data = {
            "reason": reason,
            "mod": str(ctx.author),
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "warn_id": len(self.warns[member.id]) + 1
        }
        self.warns[member.id].append(warn_data)
        
        embed = discord.Embed(title="⚠️ Warning", description=f"{member.mention} has been warned.\nReason: {reason}\nWarning ID: {warn_data['warn_id']}", color=discord.Color.orange())
        await ctx.send(embed=embed)
        
        # Optional: DM to member
        try:
            await member.send(f"📢 You have been warned on **{ctx.guild.name}**.\nReason: {reason}")
        except:
            pass

    # ========== WORD FILTER ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wordfilter(self, ctx, action, *, word=None):
        """!wordfilter add <word> | !wordfilter remove <word> | !wordfilter list"""
        if action == "add" and word:
            if word.lower() not in self.bad_words:
                self.bad_words.append(word.lower())
                await ctx.send(f"✅ `{word}` has been added to the filter list.")
            else:
                await ctx.send(f"⚠️ `{word}` is already in the list.")
        
        elif action == "remove" and word:
            if word.lower() in self.bad_words:
                self.bad_words.remove(word.lower())
                await ctx.send(f"✅ `{word}` has been removed from the filter list.")
            else:
                await ctx.send(f"⚠️ `{word}` not found in the list.")
        
        elif action == "list":
            if self.bad_words:
                await ctx.send(f"📋 **Filtered words:** {', '.join(self.bad_words)}")
            else:
                await ctx.send("📋 No words are being filtered.")
        
        else:
            await ctx.send("❌ Usage: `!wordfilter add <word>` | `!wordfilter remove <word>` | `!wordfilter list`")

    # ========== WORD FILTER LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        content_lower = message.content.lower()
        for bad_word in self.bad_words:
            if bad_word in content_lower:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, that word is not allowed!", delete_after=5)
                break

    # ========== LOG ACTION HELPER ==========
    async def log_action(self, ctx, action, member, reason):
        if self.log_channel_id:
            channel = ctx.guild.get_channel(self.log_channel_id)
            if channel:
                embed = discord.Embed(title=f"📋 {action}", description=f"**Member:** {member.mention}\n**Reason:** {reason}\n**Mod:** {ctx.author.mention}", color=discord.Color.blue(), timestamp=datetime.now())
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
