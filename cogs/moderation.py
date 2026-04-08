import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "moderation_data.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_server_data(self, guild_id):
        if str(guild_id) not in self.data:
            self.data[str(guild_id)] = {
                "jail_role": None,
                "jailed_users": [],
                "wordfilter_words": [],
                "warns": {}
            }
            self.save_data()
        return self.data[str(guild_id)]

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
        else:
            embed.set_footer(text="Moderation System")
        return embed

    async def is_mod(self, ctx):
        if not ctx.author.guild_permissions.kick_members and not ctx.author.guild_permissions.ban_members:
            embed = self.create_embed(
                "⛔ Permission Denied",
                "You need `Kick Members` or `Ban Members` permission to use this command.",
                0xED4245
            )
            await ctx.send(embed=embed)
            return False
        return True

    async def find_member(self, ctx, member_str):
        member = None
        # Try as ID
        if member_str.isdigit():
            member = ctx.guild.get_member(int(member_str))
        # Try to clean mention format <@!123> or <@123>
        if not member:
            clean = member_str.strip('<@!>')
            if clean.isdigit():
                member = ctx.guild.get_member(int(clean))
        # Try by name or display name (case-insensitive)
        if not member:
            for m in ctx.guild.members:
                if m.name.lower() == member_str.lower() or m.display_name.lower() == member_str.lower():
                    member = m
                    break
        return member

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.ban(reason=reason)
        embed = self.create_embed(
            "🔨 User Banned",
            f"{member.mention} has been permanently banned.",
            0xED4245,
            fields=[
                ("📝 Reason", reason, False),
                ("👮 Moderator", ctx.author.mention, True),
                ("🆔 User ID", str(member.id), True)
            ],
            footer=f"Banned by {ctx.author}"
        )
        await ctx.send(embed=embed)

    @commands.command(name="clearnick")
    @commands.has_permissions(manage_nicknames=True)
    async def clear_nick(self, ctx, member: discord.Member):
        old_nick = member.display_name
        await member.edit(nick=None)
        embed = self.create_embed(
            "✏️ Nickname Cleared",
            f"Nickname reset for {member.mention}",
            0x57F287,
            fields=[
                ("📛 Previous Nickname", old_nick, False),
                ("👮 Moderator", ctx.author.mention, True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="drag")
    @commands.has_permissions(move_members=True)
    async def drag(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        if member.voice and member.voice.channel:
            old_channel = member.voice.channel
            await member.move_to(channel)
            embed = self.create_embed(
                "🎤 Member Moved",
                f"{member.mention} has been moved.",
                0x57F287,
                fields=[
                    ("📍 From", old_channel.mention, True),
                    ("🎯 To", channel.mention, True),
                    ("👮 Moderator", ctx.author.mention, True)
                ]
            )
            await ctx.send(embed=embed)
        else:
            embed = self.create_embed(
                "❌ Move Failed",
                f"{member.mention} is not in a voice channel.",
                0xED4245
            )
            await ctx.send(embed=embed)

    @commands.command(name="history")
    @commands.has_permissions(view_audit_log=True)
    async def history(self, ctx, member: discord.Member = None, limit=10):
        if not member:
            embed = self.create_embed(
                "❌ Missing Argument",
                "Please specify a member.\nUsage: `!history @user [limit]`",
                0xED4245
            )
            await ctx.send(embed=embed)
            return
        embed = self.create_embed(
            "📜 Moderation History",
            f"Showing last {limit} actions for {member.display_name}",
            0x2b2d31,
            footer="Use audit log for full details"
        )
        await ctx.send(embed=embed)

    @commands.command(name="historychannel")
    @commands.has_permissions(manage_channels=True)
    async def historychannel(self, ctx, channel: discord.TextChannel = None, limit=10):
        channel = channel or ctx.channel
        embed = self.create_embed(
            "📜 Channel History",
            f"Message history for {channel.mention}",
            0x2b2d31,
            footer="Use a logging bot for persistent history"
        )
        await ctx.send(embed=embed)

    @commands.command(name="jail-list")
    @commands.has_permissions(moderate_members=True)
    async def jail_list(self, ctx):
        data = self.get_server_data(ctx.guild.id)
        jailed = data.get("jailed_users", [])
        if not jailed:
            embed = self.create_embed(
                "⛓️ Jail List",
                "No members are currently jailed.",
                0xFEE75C
            )
        else:
            members_list = "\n".join([f"<@{uid}>" for uid in jailed])
            embed = self.create_embed(
                "⛓️ Jailed Members",
                members_list,
                0x2b2d31,
                footer=f"Total: {len(jailed)} jailed users"
            )
        await ctx.send(embed=embed)

    @commands.command(name="jail-settings")
    @commands.has_permissions(administrator=True)
    async def jail_settings(self, ctx, role: discord.Role = None):
        data = self.get_server_data(ctx.guild.id)
        if role:
            data["jail_role"] = role.id
            self.save_data()
            embed = self.create_embed(
                "⚙️ Jail Role Set",
                f"Jail role has been set to {role.mention}",
                0x57F287
            )
        else:
            role_id = data.get("jail_role")
            if role_id:
                r = ctx.guild.get_role(role_id)
                embed = self.create_embed(
                    "⚙️ Current Jail Role",
                    f"{r.mention if r else 'None (role not found)'}",
                    0x2b2d31
                )
            else:
                embed = self.create_embed(
                    "⚠️ No Jail Role Set",
                    "Use `!jail-settings @role` to configure.",
                    0xFEE75C
                )
        await ctx.send(embed=embed)

    @commands.command(name="jail")
    @commands.has_permissions(moderate_members=True)
    async def jail(self, ctx, member: discord.Member, *, reason="No reason"):
        data = self.get_server_data(ctx.guild.id)
        jail_role_id = data.get("jail_role")
        if not jail_role_id:
            embed = self.create_embed(
                "❌ Jail Role Not Set",
                "Use `!jail-settings @role` first.",
                0xED4245
            )
            await ctx.send(embed=embed)
            return
        jail_role = ctx.guild.get_role(jail_role_id)
        if not jail_role:
            embed = self.create_embed(
                "❌ Jail Role Missing",
                "The configured jail role no longer exists. Please reconfigure.",
                0xED4245
            )
            await ctx.send(embed=embed)
            return
        await member.add_roles(jail_role, reason=reason)
        if str(member.id) not in data["jailed_users"]:
            data["jailed_users"].append(str(member.id))
            self.save_data()
        embed = self.create_embed(
            "⛓️ User Jailed",
            f"{member.mention} has been jailed.",
            0xFEE75C,
            fields=[
                ("📝 Reason", reason, False),
                ("👮 Moderator", ctx.author.mention, True),
                ("🔒 Jail Role", jail_role.mention, True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason"):
        await member.kick(reason=reason)
        embed = self.create_embed(
            "👢 User Kicked",
            f"{member.mention} has been kicked from the server.",
            0xED4245,
            fields=[
                ("📝 Reason", reason, False),
                ("👮 Moderator", ctx.author.mention, True),
                ("🆔 User ID", str(member.id), True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = self.create_embed(
            "🔒 Channel Locked",
            f"{channel.mention} has been locked.",
            0xED4245,
            fields=[
                ("👮 Moderator", ctx.author.mention, True),
                ("📢 Note", "Members can no longer send messages.", False)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="moveall")
    @commands.has_permissions(move_members=True)
    async def moveall(self, ctx, from_channel: discord.VoiceChannel, to_channel: discord.VoiceChannel):
        count = 0
        for member in from_channel.members:
            await member.move_to(to_channel)
            count += 1
        embed = self.create_embed(
            "🔄 Mass Member Move",
            f"Moved {count} members.",
            0x57F287,
            fields=[
                ("📍 From", from_channel.mention, True),
                ("🎯 To", to_channel.mention, True),
                ("👮 Moderator", ctx.author.mention, True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="nickname", aliases=["nick"])
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, new_nick=None):
        old_nick = member.display_name
        if new_nick:
            await member.edit(nick=new_nick[:32])
            embed = self.create_embed(
                "✏️ Nickname Changed",
                f"Nickname updated for {member.mention}",
                0x57F287,
                fields=[
                    ("📛 Before", old_nick, True),
                    ("✨ After", new_nick[:32], True),
                    ("👮 Moderator", ctx.author.mention, True)
                ]
            )
        else:
            await member.edit(nick=None)
            embed = self.create_embed(
                "✏️ Nickname Reset",
                f"Nickname reset for {member.mention}",
                0x57F287,
                fields=[
                    ("📛 Previous Nickname", old_nick, False),
                    ("👮 Moderator", ctx.author.mention, True)
                ]
            )
        await ctx.send(embed=embed)

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        if amount < 1 or amount > 100:
            embed = self.create_embed(
                "❌ Invalid Amount",
                "Amount must be between 1 and 100.",
                0xED4245
            )
            await ctx.send(embed=embed)
            return
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = self.create_embed(
            "🧹 Messages Purged",
            f"Successfully deleted {len(deleted)-1} messages.",
            0x57F287,
            fields=[
                ("📊 Channel", ctx.channel.mention, True),
                ("👮 Moderator", ctx.author.mention, True)
            ]
        )
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=3)

    @commands.command(name="role", aliases=["r"])
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member_str: str, role_str: str, action: str = None):
        """
        Add or remove a role from a member.
        Usage: !r @user mod          (auto-detects add/remove)
               !r @user "Moderator"  (role with spaces in quotes)
               !r add @user mod      (explicit add)
               !r remove @user mod   (explicit remove)
        """
        
        # Find member
        member = await self.find_member(ctx, member_str)
        if not member:
            embed = self.create_embed(
                "❌ Member not found",
                f"Could not find `{member_str}`. Use @mention, User ID, or exact name.",
                0xED4245
            )
            await ctx.send(embed=embed)
            return
        
        # Find role by name (without @) or mention
        role = None
        # Remove @ if user accidentally added it
        clean_role_str = role_str.strip('<@&>').strip()
        
        # Try exact match
        for r in ctx.guild.roles:
            if r.name.lower() == clean_role_str.lower():
                role = r
                break
        
        # If not found, try partial match (starts with)
        if not role:
            for r in ctx.guild.roles:
                if r.name.lower().startswith(clean_role_str.lower()):
                    role = r
                    break
        
        if not role:
            role_list = [r.name for r in ctx.guild.roles if r.name != '@everyone'][:10]
            embed = self.create_embed(
                "❌ Role not found",
                f"Could not find role `{role_str}`.\nAvailable roles: `{', '.join(role_list)}`" + ("..." if len(ctx.guild.roles) > 11 else ""),
                0xED4245
            )
            await ctx.send(embed=embed)
            return
        
        # Determine action (auto-detect if not specified)
        if action is None:
            # Auto-detect: if member has role -> remove, else -> add
            if role in member.roles:
                action = "remove"
            else:
                action = "add"
        else:
            action = action.lower()
        
        # Execute action
        if action == "add":
            if role in member.roles:
                embed = self.create_embed(
                    "⚠️ Already Has Role",
                    f"{member.mention} already has the role {role.mention}.",
                    0xFEE75C
                )
            else:
                await member.add_roles(role)
                embed = self.create_embed(
                    "➕ Role Added",
                    f"Added {role.mention} to {member.mention}",
                    0x57F287,
                    fields=[
                        ("👤 User", member.mention, True),
                        ("🎭 Role", role.mention, True),
                        ("👮 Moderator", ctx.author.mention, True)
                    ]
                )
        elif action == "remove":
            if role not in member.roles:
                embed = self.create_embed(
                    "⚠️ Doesn't Have Role",
                    f"{member.mention} does not have the role {role.mention}.",
                    0xFEE75C
                )
            else:
                await member.remove_roles(role)
                embed = self.create_embed(
                    "➖ Role Removed",
                    f"Removed {role.mention} from {member.mention}",
                    0x57F287,
                    fields=[
                        ("👤 User", member.mention, True),
                        ("🎭 Role", role.mention, True),
                        ("👮 Moderator", ctx.author.mention, True)
                    ]
                )
        else:
            embed = self.create_embed(
                "❌ Invalid Action",
                "Use `add`, `remove`, or let the bot auto-detect.\nExample: `!r @user mod`",
                0xED4245
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="roles")
    @commands.has_permissions(manage_roles=True)
    async def list_roles(self, ctx):
        roles = [r.mention for r in ctx.guild.roles if r.name != "@everyone"]
        if not roles:
            embed = self.create_embed("📋 Server Roles", "No roles found.", 0xFEE75C)
            await ctx.send(embed=embed)
        else:
            # Split into chunks of 20 to avoid embed limits
            chunks = [roles[i:i+20] for i in range(0, len(roles), 20)]
            for i, chunk in enumerate(chunks):
                embed = self.create_embed(
                    f"📋 Server Roles (Page {i+1}/{len(chunks)})",
                    ", ".join(chunk),
                    0x2b2d31,
                    footer=f"Total: {len(roles)} roles"
                )
                await ctx.send(embed=embed)

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        if seconds < 0 or seconds > 21600:
            embed = self.create_embed(
                "❌ Invalid Slowmode",
                "Slowmode must be between 0 and 21600 seconds (6 hours).",
                0xED4245
            )
            await ctx.send(embed=embed)
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            embed = self.create_embed(
                "⏩ Slowmode Disabled",
                f"Slowmode has been turned off in {ctx.channel.mention}",
                0x57F287
            )
        else:
            embed = self.create_embed(
                "🐢 Slowmode Enabled",
                f"Slowmode set to {seconds} seconds in {ctx.channel.mention}",
                0x57F287,
                fields=[
                    ("⏱️ Delay", f"{seconds} seconds", True),
                    ("👮 Moderator", ctx.author.mention, True)
                ]
            )
        await ctx.send(embed=embed)

    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason="No reason"):
        if duration <= 0:
            embed = self.create_embed("❌ Invalid Duration", "Duration must be positive.", 0xED4245)
            await ctx.send(embed=embed)
            return
        until = datetime.utcnow() + timedelta(minutes=min(duration, 40320))
        await member.timeout(until, reason=reason)
        embed = self.create_embed(
            "⏰ User Timed Out",
            f"{member.mention} has been timed out.",
            0xFEE75C,
            fields=[
                ("⏱️ Duration", f"{duration} minutes", True),
                ("📝 Reason", reason, False),
                ("👮 Moderator", ctx.author.mention, True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user_name_or_id):
        banned_users = [entry async for entry in ctx.guild.bans()]
        user = None
        for ban_entry in banned_users:
            ban_user = ban_entry.user
            if str(ban_user.id) == user_name_or_id or str(ban_user) == user_name_or_id:
                user = ban_user
                break
        if user:
            await ctx.guild.unban(user)
            embed = self.create_embed(
                "✅ User Unbanned",
                f"{user.mention} has been unbanned.",
                0x57F287,
                fields=[("👮 Moderator", ctx.author.mention, True)]
            )
        else:
            embed = self.create_embed(
                "❌ User Not Found",
                "User not found in ban list.",
                0xED4245
            )
        await ctx.send(embed=embed)

    @commands.command(name="unjail")
    @commands.has_permissions(moderate_members=True)
    async def unjail(self, ctx, member: discord.Member):
        data = self.get_server_data(ctx.guild.id)
        jail_role_id = data.get("jail_role")
        if jail_role_id:
            jail_role = ctx.guild.get_role(jail_role_id)
            if jail_role and jail_role in member.roles:
                await member.remove_roles(jail_role)
        if str(member.id) in data["jailed_users"]:
            data["jailed_users"].remove(str(member.id))
            self.save_data()
        embed = self.create_embed(
            "🔓 User Unjailed",
            f"{member.mention} has been released from jail.",
            0x57F287,
            fields=[("👮 Moderator", ctx.author.mention, True)]
        )
        await ctx.send(embed=embed)

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = self.create_embed(
            "🔓 Channel Unlocked",
            f"{channel.mention} has been unlocked.",
            0x57F287,
            fields=[("👮 Moderator", ctx.author.mention, True)]
        )
        await ctx.send(embed=embed)

    @commands.command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        await member.timeout(None)
        embed = self.create_embed(
            "✅ Timeout Removed",
            f"Timeout has been removed from {member.mention}.",
            0x57F287,
            fields=[("👮 Moderator", ctx.author.mention, True)]
        )
        await ctx.send(embed=embed)

    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason"):
        data = self.get_server_data(ctx.guild.id)
        warns = data["warns"]
        if str(member.id) not in warns:
            warns[str(member.id)] = []
        warns[str(member.id)].append({
            "reason": reason,
            "moderator": str(ctx.author),
            "date": str(datetime.utcnow())
        })
        self.save_data()
        embed = self.create_embed(
            "⚠️ User Warned",
            f"{member.mention} has received a warning.",
            0xFEE75C,
            fields=[
                ("📝 Reason", reason, False),
                ("👮 Moderator", ctx.author.mention, True),
                ("⚠️ Total Warnings", str(len(warns[str(member.id)])), True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="wordfilter")
    @commands.has_permissions(manage_messages=True)
    async def wordfilter(self, ctx, action: str, *, word=None):
        data = self.get_server_data(ctx.guild.id)
        if action == "add":
            if word:
                data["wordfilter_words"].append(word.lower())
                self.save_data()
                embed = self.create_embed(
                    "🚫 Word Added to Filter",
                    f"`{word}` will now be filtered.",
                    0x57F287,
                    fields=[("📝 Word", word, True)]
                )
            else:
                embed = self.create_embed("❌ Missing Word", "Specify a word to add.", 0xED4245)
        elif action == "remove":
            if word and word.lower() in data["wordfilter_words"]:
                data["wordfilter_words"].remove(word.lower())
                self.save_data()
                embed = self.create_embed(
                    "✅ Word Removed from Filter",
                    f"`{word}` is no longer filtered.",
                    0x57F287
                )
            else:
                embed = self.create_embed("❌ Word Not Found", "Word not in filter list.", 0xED4245)
        elif action == "list":
            words = data["wordfilter_words"]
            if words:
                embed = self.create_embed(
                    "📋 Word Filter List",
                    ", ".join(words),
                    0x2b2d31,
                    footer=f"Total: {len(words)} filtered words"
                )
            else:
                embed = self.create_embed("📋 Word Filter List", "No words in filter.", 0xFEE75C)
        else:
            embed = self.create_embed(
                "❌ Invalid Action",
                "Use `add`, `remove`, or `list`.\nExample: `!wordfilter add badword`",
                0xED4245
            )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        data = self.get_server_data(message.guild.id)
        filtered = data.get("wordfilter_words", [])
        if any(word in message.content.lower() for word in filtered):
            await message.delete()
            embed = self.create_embed(
                "🚫 Filtered Word Detected",
                f"{message.author.mention}, your message contained a filtered word and has been deleted.",
                0xED4245
            )
            warn_msg = await message.channel.send(embed=embed)
            await warn_msg.delete(delay=5)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
