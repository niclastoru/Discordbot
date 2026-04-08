import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import asyncio
import random

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "admin_data.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "disabled_commands": {},  # {guild_id: [command_names]}
                "auto_responders": {},    # {guild_id: {trigger: response}}
                "sticky_messages": {},    # {guild_id: {channel_id: message_id}}
                "reaction_roles": {},     # {guild_id: {message_id: {emoji: role_id}}}
                "antinuke": False,
                "antiraid": False,
                "settings": {}
            }
        self.save_data()

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_guild_data(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.data["disabled_commands"]:
            self.data["disabled_commands"][guild_id] = []
        if guild_id not in self.data["auto_responders"]:
            self.data["auto_responders"][guild_id] = {}
        if guild_id not in self.data["sticky_messages"]:
            self.data["sticky_messages"][guild_id] = {}
        if guild_id not in self.data["reaction_roles"]:
            self.data["reaction_roles"][guild_id] = {}
        if guild_id not in self.data["settings"]:
            self.data["settings"][guild_id] = {
                "mod_log": None,
                "welcome_channel": None,
                "leave_channel": None
            }
        if "antinuke" not in self.data:
            self.data["antinuke"] = False
        if "antiraid" not in self.data:
            self.data["antiraid"] = False
        self.save_data()
        return {
            "disabled_commands": self.data["disabled_commands"][guild_id],
            "auto_responders": self.data["auto_responders"][guild_id],
            "sticky_messages": self.data["sticky_messages"][guild_id],
            "reaction_roles": self.data["reaction_roles"][guild_id],
            "settings": self.data["settings"][guild_id]
        }

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
            embed.set_footer(text="Admin System")
        return embed

    async def is_admin(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            embed = self.create_embed(
                "⛔ Permission Denied",
                "You need `Administrator` permission to use this command.",
                0xED4245
            )
            await ctx.send(embed=embed)
            return False
        return True

    # ========== COMMANDS ==========

    @commands.command(name="activity")
    @commands.has_permissions(administrator=True)
    async def set_activity(self, ctx, typ: str, *, name: str):
        """Set bot activity. Types: playing, watching, listening, streaming"""
        typ = typ.lower()
        activity = None
        
        if typ == "playing":
            activity = discord.Game(name=name)
        elif typ == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=name)
        elif typ == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=name)
        elif typ == "streaming":
            activity = discord.Streaming(name=name, url="https://twitch.tv/example")
        else:
            embed = self.create_embed("❌ Invalid Type", "Use: playing, watching, listening, streaming", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        await self.bot.change_presence(activity=activity)
        embed = self.create_embed("✅ Activity Updated", f"Now {typ}: {name}", 0x57F287)
        await ctx.send(embed=embed)

    @commands.command(name="announce")
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send an announcement to a channel"""
        embed = self.create_embed(
            "📢 Announcement",
            message,
            0x57F287,
            footer=f"Announced by {ctx.author}"
        )
        await channel.send(embed=embed)
        await ctx.send(embed=self.create_embed("✅ Announcement Sent", f"Sent to {channel.mention}", 0x57F287))

    @commands.command(name="antinuke")
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx, mode: str = None):
        """Enable/disable anti-nuke protection"""
        if mode is None:
            status = "enabled" if self.data["antinuke"] else "disabled"
            embed = self.create_embed("🛡️ Anti-Nuke", f"Currently **{status}**", 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        if mode.lower() == "on":
            self.data["antinuke"] = True
            self.save_data()
            embed = self.create_embed("🛡️ Anti-Nuke Enabled", "Server is now protected against nuke attacks", 0x57F287)
        elif mode.lower() == "off":
            self.data["antinuke"] = False
            self.save_data()
            embed = self.create_embed("🛡️ Anti-Nuke Disabled", "Server protection turned off", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Mode", "Use `on` or `off`", 0xED4245)
        await ctx.send(embed=embed)

    @commands.command(name="antiraid")
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, mode: str = None):
        """Enable/disable anti-raid protection"""
        if mode is None:
            status = "enabled" if self.data["antiraid"] else "disabled"
            embed = self.create_embed("🛡️ Anti-Raid", f"Currently **{status}**", 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        if mode.lower() == "on":
            self.data["antiraid"] = True
            self.save_data()
            embed = self.create_embed("🛡️ Anti-Raid Enabled", "Server is now protected against raids", 0x57F287)
        elif mode.lower() == "off":
            self.data["antiraid"] = False
            self.save_data()
            embed = self.create_embed("🛡️ Anti-Raid Disabled", "Server protection turned off", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Mode", "Use `on` or `off`", 0xED4245)
        await ctx.send(embed=embed)

    @commands.command(name="autoresponder")
    @commands.has_permissions(administrator=True)
    async def autoresponder(self, ctx, action: str, trigger: str = None, *, response: str = None):
        """Manage auto-responders. Usage: !autoresponder add hello Hi there! or !autoresponder remove hello"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if action.lower() == "add":
            if not trigger or not response:
                embed = self.create_embed("❌ Missing Arguments", "Usage: `!autoresponder add trigger response`", 0xED4245)
                await ctx.send(embed=embed)
                return
            guild_data["auto_responders"][trigger.lower()] = response
            self.save_data()
            embed = self.create_embed("✅ Auto-Responder Added", f"`{trigger}` → `{response}`", 0x57F287)
        
        elif action.lower() == "remove":
            if not trigger:
                embed = self.create_embed("❌ Missing Trigger", "Usage: `!autoresponder remove trigger`", 0xED4245)
                await ctx.send(embed=embed)
                return
            if trigger.lower() in guild_data["auto_responders"]:
                del guild_data["auto_responders"][trigger.lower()]
                self.save_data()
                embed = self.create_embed("✅ Auto-Responder Removed", f"Removed `{trigger}`", 0x57F287)
            else:
                embed = self.create_embed("❌ Not Found", f"Trigger `{trigger}` not found", 0xED4245)
        
        elif action.lower() == "list":
            responders = guild_data["auto_responders"]
            if not responders:
                embed = self.create_embed("📋 Auto-Responders", "No auto-responders set up.", 0xFEE75C)
            else:
                text = "\n".join([f"`{k}` → {v[:50]}" for k, v in responders.items()])
                embed = self.create_embed("📋 Auto-Responders", text[:4000], 0x2b2d31, footer=f"Total: {len(responders)}")
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add`, `remove`, or `list`", 0xED4245)
        
        await ctx.send(embed=embed)

    @commands.command(name="customize")
    @commands.has_permissions(administrator=True)
    async def customize(self, ctx, setting: str, *, value: str = None):
        """Customize bot settings. Usage: !customize prefix ! or !customize mod-log #channel"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if setting.lower() == "prefix":
            if value:
                # Note: Changing prefix requires bot restart or custom prefix system
                embed = self.create_embed("⚙️ Prefix Change", f"Prefix would be changed to `{value}`. Requires bot restart.", 0xFEE75C)
            else:
                embed = self.create_embed("⚙️ Current Prefix", f"Current prefix: `!`", 0x2b2d31)
        
        elif setting.lower() == "mod-log":
            if value:
                channel = discord.utils.get(ctx.guild.text_channels, name=value.strip("#"))
                if channel:
                    guild_data["settings"]["mod_log"] = channel.id
                    self.save_data()
                    embed = self.create_embed("✅ Mod-Log Set", f"Moderation log channel: {channel.mention}", 0x57F287)
                else:
                    embed = self.create_embed("❌ Channel Not Found", f"Could not find channel `{value}`", 0xED4245)
            else:
                channel_id = guild_data["settings"]["mod_log"]
                channel = ctx.guild.get_channel(channel_id) if channel_id else None
                embed = self.create_embed("⚙️ Mod-Log Channel", f"{channel.mention if channel else 'Not set'}", 0x2b2d31)
        else:
            embed = self.create_embed("❌ Unknown Setting", "Available: `prefix`, `mod-log`", 0xED4245)
        
        await ctx.send(embed=embed)

    @commands.command(name="disablecommand")
    @commands.has_permissions(administrator=True)
    async def disable_command(self, ctx, *, command_name: str):
        """Disable a command on this server"""
        guild_data = self.get_guild_data(ctx.guild.id)
        cmd = self.bot.get_command(command_name.lower())
        
        if not cmd:
            embed = self.create_embed("❌ Command Not Found", f"`{command_name}` does not exist", 0xED4245)
        elif command_name in guild_data["disabled_commands"]:
            embed = self.create_embed("⚠️ Already Disabled", f"`{command_name}` is already disabled", 0xFEE75C)
        else:
            guild_data["disabled_commands"].append(command_name)
            self.save_data()
            embed = self.create_embed("🔒 Command Disabled", f"`{command_name}` has been disabled on this server", 0xED4245)
        
        await ctx.send(embed=embed)

    @commands.command(name="enablecommand")
    @commands.has_permissions(administrator=True)
    async def enable_command(self, ctx, *, command_name: str):
        """Enable a command on this server"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if command_name in guild_data["disabled_commands"]:
            guild_data["disabled_commands"].remove(command_name)
            self.save_data()
            embed = self.create_embed("🔓 Command Enabled", f"`{command_name}` has been enabled on this server", 0x57F287)
        else:
            embed = self.create_embed("⚠️ Not Disabled", f"`{command_name}` is not disabled", 0xFEE75C)
        
        await ctx.send(embed=embed)

    @commands.command(name="dmall")
    @commands.has_permissions(administrator=True)
    async def dm_all(self, ctx, *, message: str):
        """DM all members in the server (use with caution)"""
        embed = self.create_embed(
            "⚠️ Confirmation",
            f"Are you sure you want to DM **{len(ctx.guild.members)}** members?\nThis will send:\n`{message[:100]}`\n\nReply with `yes` to confirm.",
            0xFEE75C
        )
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"
        
        try:
            await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("❌ Cancelled", "DM all cancelled", 0xED4245))
            return
        
        success = 0
        failed = 0
        
        for member in ctx.guild.members:
            if not member.bot:
                try:
                    await member.send(message)
                    success += 1
                except:
                    failed += 1
            await asyncio.sleep(1)  # Rate limit protection
        
        embed = self.create_embed(
            "📬 DM All Complete",
            f"✅ Success: {success}\n❌ Failed: {failed}",
            0x57F287
        )
        await ctx.send(embed=embed)

    @commands.command(name="fakepermissions")
    @commands.has_permissions(administrator=True)
    async def fake_permissions(self, ctx, member: discord.Member = None):
        """Show fake permission list (info only)"""
        member = member or ctx.author
        perms = [perm for perm, value in member.guild_permissions if value]
        
        embed = self.create_embed(
            f"🛡️ {member.display_name}'s Permissions",
            "\n".join([f"✅ {p}" for p in perms[:25]]) if perms else "No permissions",
            0x2b2d31,
            footer=f"Total: {len(perms)} permissions"
        )
        await ctx.send(embed=embed)

    @commands.command(name="listpermissions")
    @commands.has_permissions(administrator=True)
    async def list_permissions(self, ctx, role: discord.Role = None):
        """List all permissions for a role or yourself"""
        target = role or ctx.author
        perms = target.permissions if role else target.guild_permissions
        perms_list = [perm for perm, value in perms if value]
        
        embed = self.create_embed(
            f"📋 Permissions for {target.name}",
            "\n".join([f"✅ {p}" for p in perms_list[:25]]) if perms_list else "No permissions",
            0x2b2d31,
            footer=f"Total: {len(perms_list)} permissions"
        )
        await ctx.send(embed=embed)

    @commands.command(name="nuke")
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """Delete and recreate a channel (clears all messages)"""
        channel = channel or ctx.channel
        new_channel = await channel.clone()
        await channel.delete()
        
        embed = self.create_embed(
            "💥 Channel Nuked",
            f"{new_channel.mention} has been nuked by {ctx.author.mention}",
            0xED4245
        )
        await new_channel.send(embed=embed)

    @commands.command(name="reaction-setup")
    @commands.has_permissions(administrator=True)
    async def reaction_setup(self, ctx, message_id: int, emoji: str, role: discord.Role):
        """Setup reaction role. Usage: !reaction-setup 1234567890 🎭 @Role"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        try:
            message = await ctx.channel.fetch_message(message_id)
            guild_data["reaction_roles"][str(message.id)] = guild_data["reaction_roles"].get(str(message.id), {})
            guild_data["reaction_roles"][str(message.id)][emoji] = role.id
            self.save_data()
            
            await message.add_reaction(emoji)
            embed = self.create_embed("✅ Reaction Role Setup", f"{emoji} → {role.mention} on [message]({message.jump_url})", 0x57F287)
        except discord.NotFound:
            embed = self.create_embed("❌ Message Not Found", f"Message ID `{message_id}` not found in this channel", 0xED4245)
        except Exception as e:
            embed = self.create_embed("❌ Error", str(e), 0xED4245)
        
        await ctx.send(embed=embed)

    @commands.command(name="reactionroles")
    @commands.has_permissions(administrator=True)
    async def reaction_roles(self, ctx, action: str = None, message_id: int = None):
        """List or clear reaction roles"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if action == "clear" and message_id:
            if str(message_id) in guild_data["reaction_roles"]:
                del guild_data["reaction_roles"][str(message_id)]
                self.save_data()
                embed = self.create_embed("✅ Reaction Roles Cleared", f"Cleared for message ID `{message_id}`", 0x57F287)
            else:
                embed = self.create_embed("❌ Not Found", f"No reaction roles for message ID `{message_id}`", 0xED4245)
        else:
            rr_data = guild_data["reaction_roles"]
            if not rr_data:
                embed = self.create_embed("📋 Reaction Roles", "No reaction roles set up.", 0xFEE75C)
            else:
                text = "\n".join([f"Message `{mid}`: {len(emojis)} reactions" for mid, emojis in rr_data.items()])
                embed = self.create_embed("📋 Reaction Roles", text[:4000], 0x2b2d31, footer=f"Total: {len(rr_data)} messages")
        
        await ctx.send(embed=embed)

    @commands.command(name="serverrules")
    @commands.has_permissions(administrator=True)
    async def server_rules(self, ctx, *, rules: str = None):
        """Set or show server rules"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if rules:
            guild_data["settings"]["rules"] = rules
            self.save_data()
            embed = self.create_embed("📜 Server Rules Set", rules[:2000], 0x57F287)
        else:
            rules_text = guild_data["settings"].get("rules", "No rules set. Use `!serverrules <rules>` to set them.")
            embed = self.create_embed("📜 Server Rules", rules_text[:4000], 0x2b2d31)
        
        await ctx.send(embed=embed)

    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def view_settings(self, ctx):
        """View current server settings"""
        guild_data = self.get_guild_data(ctx.guild.id)
        settings = guild_data["settings"]
        
        mod_log_channel = ctx.guild.get_channel(settings.get("mod_log")) if settings.get("mod_log") else None
        
        embed = self.create_embed(
            "⚙️ Server Settings",
            "",
            0x2b2d31,
            fields=[
                ("📝 Mod-Log", mod_log_channel.mention if mod_log_channel else "Not set", True),
                ("🔧 Disabled Commands", str(len(guild_data["disabled_commands"])), True),
                ("🤖 Auto-Responders", str(len(guild_data["auto_responders"])), True),
                ("🎭 Reaction Roles", str(len(guild_data["reaction_roles"])), True),
                ("🛡️ Anti-Nuke", "Enabled" if self.data["antinuke"] else "Disabled", True),
                ("🛡️ Anti-Raid", "Enabled" if self.data["antiraid"] else "Disabled", True)
            ]
        )
        await ctx.send(embed=embed)

    @commands.command(name="status")
    @commands.has_permissions(administrator=True)
    async def status(self, ctx, *, status_text: str = None):
        """Set bot status (online, idle, dnd, invisible) or custom text"""
        if not status_text:
            embed = self.create_embed("ℹ️ Status", f"Current status: {self.bot.status}", 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible
        }
        
        if status_text.lower() in status_map:
            await self.bot.change_presence(status=status_map[status_text.lower()])
            embed = self.create_embed("✅ Status Updated", f"Bot status changed to {status_text}", 0x57F287)
        else:
            embed = self.create_embed("❌ Invalid Status", "Use: online, idle, dnd, invisible", 0xED4245)
        
        await ctx.send(embed=embed)

    @commands.command(name="stickymessage")
    @commands.has_permissions(administrator=True)
    async def sticky_message(self, ctx, action: str, *, message: str = None):
        """Set a sticky message that stays at the bottom of the channel"""
        guild_data = self.get_guild_data(ctx.guild.id)
        sticky_data = guild_data["sticky_messages"]
        
        if action.lower() == "set":
            if not message:
                embed = self.create_embed("❌ Missing Message", "Usage: `!stickymessage set Your message here`", 0xED4245)
                await ctx.send(embed=embed)
                return
            
            # Send sticky message
            sticky_msg = await ctx.send(embed=self.create_embed("📌 Sticky Message", message, 0x2b2d31))
            sticky_data[str(ctx.channel.id)] = sticky_msg.id
            self.save_data()
            embed = self.create_embed("✅ Sticky Message Set", f"[Click here]({sticky_msg.jump_url})", 0x57F287)
        
        elif action.lower() == "remove":
            if str(ctx.channel.id) in sticky_data:
                del sticky_data[str(ctx.channel.id)]
                self.save_data()
                embed = self.create_embed("✅ Sticky Message Removed", "The sticky message has been removed", 0x57F287)
            else:
                embed = self.create_embed("❌ No Sticky Message", "No sticky message set in this channel", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `set` or `remove`", 0xED4245)
        
        await ctx.send(embed=embed)

    @commands.command(name="stripstaff")
    @commands.has_permissions(administrator=True)
    async def strip_staff(self, ctx, member: discord.Member):
        """Remove all staff/administrative roles from a member"""
        staff_roles = ["Admin", "Mod", "Moderator", "Staff", "Manager", "Owner"]
        removed = []
        
        for role in member.roles[:]:
            if role.name in staff_roles or role.permissions.administrator or role.permissions.kick_members:
                await member.remove_roles(role)
                removed.append(role.name)
        
        if removed:
            embed = self.create_embed("👔 Staff Roles Removed", f"Removed from {member.mention}: {', '.join(removed)}", 0xED4245)
        else:
            embed = self.create_embed("ℹ️ No Staff Roles", f"{member.mention} has no staff roles", 0xFEE75C)
        
        await ctx.send(embed=embed)

    @commands.command(name="unbanall")
    @commands.has_permissions(administrator=True)
    async def unban_all(self, ctx):
        """Unban all banned users from the server"""
        embed = self.create_embed(
            "⚠️ Confirmation",
            f"Are you sure you want to unban **ALL** banned users?\nReply with `yes` to confirm.",
            0xFEE75C
        )
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"
        
        try:
            await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("❌ Cancelled", "Unban all cancelled", 0xED4245))
            return
        
        bans = [entry async for entry in ctx.guild.bans()]
        success = 0
        
        for ban_entry in bans:
            try:
                await ctx.guild.unban(ban_entry.user)
                success += 1
                await asyncio.sleep(1)
            except:
                pass
        
        embed = self.create_embed("✅ Unbanned All", f"Successfully unbanned **{success}** users", 0x57F287)
        await ctx.send(embed=embed)

    @commands.command(name="unjaiall")
    @commands.has_permissions(administrator=True)
    async def unjail_all(self, ctx):
        """Remove jail role from all members"""
        jail_role_name = "Jailed"
        jail_role = discord.utils.get(ctx.guild.roles, name=jail_role_name)
        
        if not jail_role:
            embed = self.create_embed("❌ No Jail Role", f"No role named `{jail_role_name}` found", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        count = 0
        for member in ctx.guild.members:
            if jail_role in member.roles:
                await member.remove_roles(jail_role)
                count += 1
                await asyncio.sleep(0.5)
        
        embed = self.create_embed("🔓 Unjailed All", f"Removed jail role from **{count}** members", 0x57F287)
        await ctx.send(embed=embed)

    @commands.command(name="vanity-url")
    @commands.has_permissions(administrator=True)
    async def vanity_url(self, ctx):
        """Show server vanity URL (if available)"""
        if ctx.guild.vanity_url_code:
            embed = self.create_embed(
                "✨ Vanity URL",
                f"discord.gg/{ctx.guild.vanity_url_code}\nUses: {ctx.guild.vanity_url_uses if ctx.guild.vanity_url_uses else 0}",
                0x57F287
            )
        else:
            embed = self.create_embed("❌ No Vanity URL", "This server doesn't have a vanity URL (requires Boost Level 3)", 0xFEE75C)
        await ctx.send(embed=embed)

    @commands.command(name="verwarnung")
    @commands.has_permissions(kick_members=True)
    async def verwarnung(self, ctx, member: discord.Member, *, grund: str = "Kein Grund"):
        """Warn a member (German for warning)"""
        # Reuse warn system from moderation
        data = {}
        data_file = "moderation_data.json"
        
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)
        
        if str(ctx.guild.id) not in data:
            data[str(ctx.guild.id)] = {"warns": {}}
        
        if "warns" not in data[str(ctx.guild.id)]:
            data[str(ctx.guild.id)]["warns"] = {}
        
        warns = data[str(ctx.guild.id)]["warns"]
        
        if str(member.id) not in warns:
            warns[str(member.id)] = []
        
        warns[str(member.id)].append({
            "reason": grund,
            "moderator": str(ctx.author),
            "date": str(datetime.utcnow())
        })
        
        with open(data_file, "w") as f:
            json.dump(data, f, indent=4)
        
        embed = self.create_embed(
            "⚠️ Verwarnung",
            f"{member.mention} wurde verwarnt",
            0xFEE75C,
            fields=[
                ("📝 Grund", grund, False),
                ("👮 Moderator", ctx.author.mention, True),
                ("⚠️ Anzahl", str(len(warns[str(member.id)])), True)
            ]
        )
        await ctx.send(embed=embed)

    # ========== EVENT HANDLERS ==========
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        guild_data = self.get_guild_data(message.guild.id)
        
        # Auto-responder
        for trigger, response in guild_data["auto_responders"].items():
            if trigger.lower() in message.content.lower():
                await message.channel.send(response)
                break
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        
        guild_data = self.get_guild_data(payload.guild_id)
        rr_data = guild_data["reaction_roles"]
        
        if str(payload.message_id) in rr_data:
            emoji = str(payload.emoji)
            if emoji in rr_data[str(payload.message_id)]:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(rr_data[str(payload.message_id)][emoji])
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    await member.add_roles(role)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild_data = self.get_guild_data(payload.guild_id)
        rr_data = guild_data["reaction_roles"]
        
        if str(payload.message_id) in rr_data:
            emoji = str(payload.emoji)
            if emoji in rr_data[str(payload.message_id)]:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(rr_data[str(payload.message_id)][emoji])
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_data = self.get_guild_data(member.guild.id)
        welcome_channel_id = guild_data["settings"].get("welcome_channel")
        
        if welcome_channel_id:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                embed = self.create_embed(
                    "👋 Welcome!",
                    f"Welcome {member.mention} to **{member.guild.name}**!",
                    0x57F287
                )
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        
        guild_data = self.get_guild_data(ctx.guild.id)
        
        # Check if command is disabled
        if isinstance(error, commands.CommandNotFound):
            return
        
        embed = self.create_embed("❌ Error", str(error), 0xED4245)
        await ctx.send(embed=embed, delete_after=10)

async def setup(bot):
    await bot.add_cog(Admin(bot))
    print("✅ Admin cog geladen")
