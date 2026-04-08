import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from database import db

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Moderation Cog geladen")

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

    async def is_mod(self, ctx):
        if not ctx.author.guild_permissions.kick_members and not ctx.author.guild_permissions.ban_members:
            embed = self.create_embed("⛔ Permission Denied", "You need `Kick Members` or `Ban Members` permission.", 0xED4245)
            await ctx.send(embed=embed)
            return False
        return True

    # ========== 1. BAN ==========
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason"):
        """Ban a member from the server"""
        await member.ban(reason=reason)
        embed = self.create_embed(
            "🔨 User Banned",
            f"{member.mention} has been permanently banned.",
            0xED4245,
            fields=[("📝 Reason", reason, False), ("👮 Moderator", ctx.author.mention, True)],
            footer=f"ID: {member.id}"
        )
        await ctx.send(embed=embed)

    # ========== 2. CLEARNICK ==========
    @commands.command(name="clearnick")
    @commands.has_permissions(manage_nicknames=True)
    async def clear_nick(self, ctx, member: discord.Member):
        """Clear a member's nickname"""
        old_nick = member.display_name
        await member.edit(nick=None)
        embed = self.create_embed("✏️ Nickname Cleared", f"Nickname reset for {member.mention}", 0x57F287,
                                  fields=[("📛 Previous", old_nick, False), ("👮 Moderator", ctx.author.mention, True)])
        await ctx.send(embed=embed)

    # ========== 3. DRAG ==========
    @commands.command(name="drag")
    @commands.has_permissions(move_members=True)
    async def drag(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        """Move a member to a different voice channel"""
        if member.voice and member.voice.channel:
            old = member.voice.channel
            await member.move_to(channel)
            embed = self.create_embed("🎤 Member Moved", f"{member.mention} moved to {channel.mention}", 0x57F287,
                                      fields=[("📍 From", old.mention, True), ("🎯 To", channel.mention, True)])
        else:
            embed = self.create_embed("❌ Move Failed", f"{member.mention} is not in a voice channel.", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 4. HISTORY ==========
    @commands.command(name="history")
    @commands.has_permissions(view_audit_log=True)
    async def history(self, ctx, member: discord.Member = None, limit: int = 10):
        """Show recent moderation actions for a member"""
        if not member:
            embed = self.create_embed("❌ Missing Member", "Usage: `!history @user`", 0xED4245)
        else:
            warns = db.get_warnings(ctx.guild.id, member.id)
            text = f"Total warnings: {len(warns)}\n\n" + "\n".join([f"• {w[3]} (by {w[4]})" for w in warns[:5]]) if warns else "No warnings"
            embed = self.create_embed(f"📜 History for {member.display_name}", text[:4000], 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 5. HISTORYCHANNEL ==========
    @commands.command(name="historychannel")
    @commands.has_permissions(manage_channels=True)
    async def history_channel(self, ctx, channel: discord.TextChannel = None, limit: int = 10):
        """Show recent messages in a channel"""
        channel = channel or ctx.channel
        embed = self.create_embed(f"📜 #{channel.name} History", f"Check manually or use logging bot.", 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 6. JAIL-LIST ==========
    @commands.command(name="jail-list")
    @commands.has_permissions(moderate_members=True)
    async def jail_list(self, ctx):
        """List all jailed members"""
        jailed = db.get_jailed_users(ctx.guild.id)
        if not jailed:
            embed = self.create_embed("⛓️ Jail List", "No members are currently jailed.", 0xFEE75C)
        else:
            members = "\n".join([f"<@{uid}>" for uid in jailed])
            embed = self.create_embed("⛓️ Jailed Members", members, 0x2b2d31, footer=f"Total: {len(jailed)}")
        await ctx.send(embed=embed)

    # ========== 7. JAIL-SETTINGS ==========
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

    # ========== 8. JAIL ==========
    @commands.command(name="jail")
    @commands.has_permissions(moderate_members=True)
    async def jail(self, ctx, member: discord.Member, *, reason="No reason"):
        """Jail a member (assign jail role)"""
        role_id = db.get_jail_role(ctx.guild.id)
        if not role_id:
            embed = self.create_embed("❌ Jail Role Not Set", "Use `!jail-settings @role` first.", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        jail_role = ctx.guild.get_role(int(role_id))
        if not jail_role:
            embed = self.create_embed("❌ Jail Role Missing", "Please reconfigure jail role.", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        await member.add_roles(jail_role, reason=reason)
        db.add_jailed_user(ctx.guild.id, member.id, reason)
        embed = self.create_embed("⛓️ User Jailed", f"{member.mention} has been jailed.", 0xFEE75C,
                                  fields=[("📝 Reason", reason, False), ("👮 Moderator", ctx.author.mention, True)])
        await ctx.send(embed=embed)

    # ========== 9. KICK ==========
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason"):
        """Kick a member from the server"""
        await member.kick(reason=reason)
        embed = self.create_embed("👢 User Kicked", f"{member.mention} has been kicked.", 0xED4245,
                                  fields=[("📝 Reason", reason, False), ("👮 Moderator", ctx.author.mention, True)])
        await ctx.send(embed=embed)

    # ========== 10. LOCK ==========
    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock a text channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = self.create_embed("🔒 Channel Locked", f"{channel.mention} has been locked.", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 11. MOVEALL ==========
    @commands.command(name="moveall")
    @commands.has_permissions(move_members=True)
    async def move_all(self, ctx, from_channel: discord.VoiceChannel, to_channel: discord.VoiceChannel):
        """Move all members from one voice channel to another"""
        count = 0
        for member in from_channel.members:
            await member.move_to(to_channel)
            count += 1
        embed = self.create_embed("🔄 Mass Member Move", f"Moved {count} members from {from_channel.mention} to {to_channel.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 12. NICKNAME ==========
    @commands.command(name="nickname", aliases=["nick"])
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, new_nick: str = None):
        """Change a member's nickname"""
        old = member.display_name
        if new_nick:
            await member.edit(nick=new_nick[:32])
            embed = self.create_embed("✏️ Nickname Changed", f"{member.mention} → `{new_nick[:32]}`", 0x57F287,
                                      fields=[("📛 Before", old, True), ("✨ After", new_nick[:32], True)])
        else:
            await member.edit(nick=None)
            embed = self.create_embed("✏️ Nickname Reset", f"Nickname reset for {member.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 13. PURGE ==========
    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Delete a number of messages (max 100)"""
        if amount < 1 or amount > 100:
            embed = self.create_embed("❌ Invalid Amount", "Amount must be between 1 and 100.", 0xED4245)
            await ctx.send(embed=embed)
            return
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = self.create_embed("🧹 Messages Purged", f"Deleted {len(deleted)-1} messages.", 0x57F287)
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=3)

    # ========== 14. ROLE (mit add/remove) ==========
    @commands.command(name="role", aliases=["r"])
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, action: str, member: discord.Member, role: discord.Role):
        """Add or remove a role. Usage: !role add @user @role or !role remove @user @role"""
        action = action.lower()
        if action == "add":
            await member.add_roles(role)
            embed = self.create_embed("➕ Role Added", f"Added {role.mention} to {member.mention}", 0x57F287)
        elif action == "remove":
            await member.remove_roles(role)
            embed = self.create_embed("➖ Role Removed", f"Removed {role.mention} from {member.mention}", 0x57F287)
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add` or `remove`.", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 15. ROLES ==========
    @commands.command(name="roles")
    @commands.has_permissions(manage_roles=True)
    async def list_roles(self, ctx):
        """List all roles in the server"""
        roles = [r.mention for r in ctx.guild.roles if r.name != "@everyone"]
        if not roles:
            embed = self.create_embed("📋 Server Roles", "No roles found.", 0xFEE75C)
        else:
            embed = self.create_embed("📋 Server Roles", ", ".join(roles[:30]), 0x2b2d31, footer=f"Total: {len(roles)}")
        await ctx.send(embed=embed)

    # ========== 16. SLOWMODE ==========
    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Set slowmode in current channel (0 to disable)"""
        if seconds < 0 or seconds > 21600:
            embed = self.create_embed("❌ Invalid Slowmode", "Must be between 0 and 21600 seconds.", 0xED4245)
        else:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                embed = self.create_embed("⏩ Slowmode Disabled", f"Slowmode turned off in {ctx.channel.mention}", 0x57F287)
            else:
                embed = self.create_embed("🐢 Slowmode Enabled", f"Set to {seconds} seconds in {ctx.channel.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 17. TIMEOUT ==========
    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason="No reason"):
        """Timeout a member (duration in minutes, max 40320)"""
        if duration <= 0:
            embed = self.create_embed("❌ Invalid Duration", "Duration must be positive.", 0xED4245)
        else:
            until = datetime.utcnow() + timedelta(minutes=min(duration, 40320))
            await member.timeout(until, reason=reason)
            embed = self.create_embed("⏰ User Timed Out", f"{member.mention} timed out for {duration} minutes.", 0xFEE75C,
                                      fields=[("📝 Reason", reason, False), ("👮 Moderator", ctx.author.mention, True)])
        await ctx.send(embed=embed)

    # ========== 18. UNBAN ==========
    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user_name_or_id):
        """Unban a user by name#discrim or user ID"""
        banned = [entry async for entry in ctx.guild.bans()]
        user = None
        for entry in banned:
            if str(entry.user.id) == user_name_or_id or str(entry.user) == user_name_or_id:
                user = entry.user
                break
        if user:
            await ctx.guild.unban(user)
            embed = self.create_embed("✅ User Unbanned", f"{user.mention} has been unbanned.", 0x57F287)
        else:
            embed = self.create_embed("❌ User Not Found", "User not found in ban list.", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 19. UNJAIL ==========
    @commands.command(name="unjail")
    @commands.has_permissions(moderate_members=True)
    async def unjail(self, ctx, member: discord.Member):
        """Remove jail role from a member"""
        role_id = db.get_jail_role(ctx.guild.id)
        if role_id:
            jail_role = ctx.guild.get_role(int(role_id))
            if jail_role and jail_role in member.roles:
                await member.remove_roles(jail_role)
        db.remove_jailed_user(ctx.guild.id, member.id)
        embed = self.create_embed("🔓 User Unjailed", f"{member.mention} has been released.", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 20. UNLOCK ==========
    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock a previously locked channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = self.create_embed("🔓 Channel Unlocked", f"{channel.mention} has been unlocked.", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 21. UNTIMEOUT ==========
    @commands.command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        """Remove timeout from a member"""
        await member.timeout(None)
        embed = self.create_embed("✅ Timeout Removed", f"Timeout removed from {member.mention}.", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 22. WARN ==========
    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason"):
        """Warn a member"""
        db.add_warning(ctx.guild.id, member.id, reason, str(ctx.author))
        warns = db.get_warnings(ctx.guild.id, member.id)
        embed = self.create_embed("⚠️ User Warned", f"{member.mention} has been warned.", 0xFEE75C,
                                  fields=[("📝 Reason", reason, False), ("👮 Moderator", ctx.author.mention, True), ("⚠️ Total", str(len(warns)), True)])
        await ctx.send(embed=embed)

    # ========== 23. WORDFILTER ==========
    @commands.command(name="wordfilter")
    @commands.has_permissions(manage_messages=True)
    async def wordfilter(self, ctx, action: str, *, word: str = None):
        """Add, remove, or list filtered words. Usage: !wordfilter add badword"""
        if action == "add" and word:
            db.add_filtered_word(ctx.guild.id, word)
            embed = self.create_embed("🚫 Word Added", f"`{word}` will now be filtered.", 0x57F287)
        elif action == "remove" and word:
            db.remove_filtered_word(ctx.guild.id, word)
            embed = self.create_embed("✅ Word Removed", f"`{word}` is no longer filtered.", 0x57F287)
        elif action == "list":
            words = db.get_filtered_words(ctx.guild.id)
            embed = self.create_embed("📋 Filtered Words", ", ".join(words) if words else "No words filtered.", 0x2b2d31)
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add`, `remove`, or `list`.", 0xED4245)
        await ctx.send(embed=embed)

    # ========== WORD FILTER LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        filtered = db.get_filtered_words(message.guild.id)
        if any(word in message.content.lower() for word in filtered):
            await message.delete()
            embed = self.create_embed("🚫 Filtered Word", f"{message.author.mention}, your message was deleted.", 0xED4245)
            msg = await message.channel.send(embed=embed)
            await msg.delete(delay=5)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
