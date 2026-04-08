import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from database import db
import aiohttp

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Admin Cog geladen")

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

    async def is_admin(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            embed = self.create_embed("⛔ Permission Denied", "You need `Administrator` permission.", 0xED4245)
            await ctx.send(embed=embed)
            return False
        return True

    # ========== 1. ACTIVITY ==========
    @commands.command(name="activity")
    @commands.has_permissions(administrator=True)
    async def activity(self, ctx, typ: str, *, name: str):
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

    # ========== 2. ANNOUNCE ==========
    @commands.command(name="announce")
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send an announcement to a channel"""
        embed = self.create_embed("📢 Announcement", message, 0x57F287, footer=f"Announced by {ctx.author}")
        await channel.send(embed=embed)
        await ctx.send(embed=self.create_embed("✅ Sent", f"Announcement sent to {channel.mention}", 0x57F287))

    # ========== 3. ANTINUKE ==========
    @commands.command(name="antinuke")
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx, mode: str = None):
        """Enable/disable anti-nuke protection"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {}).get("antinuke", False)
        
        if mode is None:
            embed = self.create_embed("🛡️ Anti-Nuke", f"Currently **{'enabled' if current else 'disabled'}**", 0x2b2d31)
        elif mode.lower() == "on":
            s = settings.get("settings", {})
            s["antinuke"] = True
            db.update_guild_settings(ctx.guild.id, "settings", s)
            embed = self.create_embed("🛡️ Anti-Nuke Enabled", "Server is now protected against nuke attacks", 0x57F287)
        elif mode.lower() == "off":
            s = settings.get("settings", {})
            s["antinuke"] = False
            db.update_guild_settings(ctx.guild.id, "settings", s)
            embed = self.create_embed("🛡️ Anti-Nuke Disabled", "Protection turned off", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Mode", "Use `on` or `off`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 4. ANTIRAID ==========
    @commands.command(name="antiraid")
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, mode: str = None):
        """Enable/disable anti-raid protection"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {}).get("antiraid", False)
        
        if mode is None:
            embed = self.create_embed("🛡️ Anti-Raid", f"Currently **{'enabled' if current else 'disabled'}**", 0x2b2d31)
        elif mode.lower() == "on":
            s = settings.get("settings", {})
            s["antiraid"] = True
            db.update_guild_settings(ctx.guild.id, "settings", s)
            embed = self.create_embed("🛡️ Anti-Raid Enabled", "Server is now protected against raids", 0x57F287)
        elif mode.lower() == "off":
            s = settings.get("settings", {})
            s["antiraid"] = False
            db.update_guild_settings(ctx.guild.id, "settings", s)
            embed = self.create_embed("🛡️ Anti-Raid Disabled", "Protection turned off", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Mode", "Use `on` or `off`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 5. AUTORESPONDER ==========
    @commands.command(name="autoresponder")
    @commands.has_permissions(administrator=True)
    async def autoresponder(self, ctx, action: str, trigger: str = None, *, response: str = None):
        """Manage auto-responders. Usage: !autoresponder add hello Hi there!"""
        settings = db.get_guild_settings(ctx.guild.id)
        responders = settings.get("auto_responders", {})
        
        if action.lower() == "add":
            if not trigger or not response:
                embed = self.create_embed("❌ Missing Arguments", "Usage: `!autoresponder add trigger response`", 0xED4245)
                await ctx.send(embed=embed)
                return
            responders[trigger.lower()] = response
            db.update_guild_settings(ctx.guild.id, "auto_responders", responders)
            embed = self.create_embed("✅ Auto-Responder Added", f"`{trigger}` → `{response}`", 0x57F287)
        
        elif action.lower() == "remove":
            if not trigger:
                embed = self.create_embed("❌ Missing Trigger", "Usage: `!autoresponder remove trigger`", 0xED4245)
                await ctx.send(embed=embed)
                return
            if trigger.lower() in responders:
                del responders[trigger.lower()]
                db.update_guild_settings(ctx.guild.id, "auto_responders", responders)
                embed = self.create_embed("✅ Auto-Responder Removed", f"Removed `{trigger}`", 0x57F287)
            else:
                embed = self.create_embed("❌ Not Found", f"Trigger `{trigger}` not found", 0xED4245)
        
        elif action.lower() == "list":
            if not responders:
                embed = self.create_embed("📋 Auto-Responders", "No auto-responders set up.", 0xFEE75C)
            else:
                text = "\n".join([f"`{k}` → {v[:50]}" for k, v in responders.items()])
                embed = self.create_embed("📋 Auto-Responders", text[:4000], 0x2b2d31, footer=f"Total: {len(responders)}")
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add`, `remove`, or `list`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 6. CUSTOMIZE AVATAR ==========
    @commands.command(name="customize avatar")
    @commands.has_permissions(administrator=True)
    async def customize_avatar(self, ctx, url: str = None):
        """Change bot avatar (provide image URL)"""
        if not url:
            embed = self.create_embed("❌ Missing URL", "Usage: `!customize avatar <image_url>`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        await self.bot.user.edit(avatar=image_data)
                        embed = self.create_embed("✅ Avatar Updated", "Bot avatar has been changed.", 0x57F287)
                    else:
                        embed = self.create_embed("❌ Failed", "Could not download image.", 0xED4245)
        except Exception as e:
            embed = self.create_embed("❌ Error", str(e), 0xED4245)
        await ctx.send(embed=embed)

    # ========== 7. CUSTOMIZE BANNER ==========
    @commands.command(name="customize banner")
    @commands.has_permissions(administrator=True)
    async def customize_banner(self, ctx, url: str = None):
        """Change bot banner (requires Discord Nitro)"""
        embed = self.create_embed("🎨 Customize Banner", "Bot banner change requires Discord Nitro on the bot account.", 0xFEE75C)
        await ctx.send(embed=embed)

    # ========== 8. CUSTOMIZE BIO ==========
    @commands.command(name="customize bio")
    @commands.has_permissions(administrator=True)
    async def customize_bio(self, ctx, *, bio: str = None):
        """Change bot about me section"""
        if not bio:
            embed = self.create_embed("❌ Missing Bio", "Usage: `!customize bio Your bio text`", 0xED4245)
        else:
            await self.bot.user.edit(bio=bio[:190])
            embed = self.create_embed("✅ Bio Updated", f"New bio: {bio[:190]}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 9. CUSTOMIZE ==========
    @commands.command(name="customize")
    @commands.has_permissions(administrator=True)
    async def customize(self, ctx, setting: str, *, value: str = None):
        """Customize bot settings. Usage: !customize prefix !"""
        if setting.lower() == "prefix":
            embed = self.create_embed("⚙️ Customize", f"Prefix change to `{value}` requires bot restart.", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Unknown Setting", "Available: `prefix`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 10. DISABLECOMMAND ==========
    @commands.command(name="disablecommand")
    @commands.has_permissions(administrator=True)
    async def disablecommand(self, ctx, *, command_name: str):
        """Disable a command on this server"""
        settings = db.get_guild_settings(ctx.guild.id)
        disabled = settings.get("disabled_commands", [])
        
        cmd = self.bot.get_command(command_name.lower())
        if not cmd:
            embed = self.create_embed("❌ Command Not Found", f"`{command_name}` does not exist", 0xED4245)
        elif command_name in disabled:
            embed = self.create_embed("⚠️ Already Disabled", f"`{command_name}` is already disabled", 0xFEE75C)
        else:
            disabled.append(command_name)
            db.update_guild_settings(ctx.guild.id, "disabled_commands", disabled)
            embed = self.create_embed("🔒 Command Disabled", f"`{command_name}` has been disabled", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 11. DMALL ==========
    @commands.command(name="dmall")
    @commands.has_permissions(administrator=True)
    async def dmall(self, ctx, *, message: str):
        """DM all members in the server (use with caution)"""
        embed = self.create_embed("⚠️ Confirmation", f"DM **{len(ctx.guild.members)}** members? Reply `yes`", 0xFEE75C)
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"
        
        try:
            await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("❌ Cancelled", "DM all cancelled", 0xED4245))
            return
        
        success, failed = 0, 0
        for member in ctx.guild.members:
            if not member.bot:
                try:
                    await member.send(message)
                    success += 1
                except:
                    failed += 1
                await asyncio.sleep(0.5)
        
        embed = self.create_embed("📬 DM All Complete", f"✅ Success: {success}\n❌ Failed: {failed}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 12. ENABLECOMMAND ==========
    @commands.command(name="enablecommand")
    @commands.has_permissions(administrator=True)
    async def enablecommand(self, ctx, *, command_name: str):
        """Enable a command on this server"""
        settings = db.get_guild_settings(ctx.guild.id)
        disabled = settings.get("disabled_commands", [])
        
        if command_name in disabled:
            disabled.remove(command_name)
            db.update_guild_settings(ctx.guild.id, "disabled_commands", disabled)
            embed = self.create_embed("🔓 Command Enabled", f"`{command_name}` has been enabled", 0x57F287)
        else:
            embed = self.create_embed("⚠️ Not Disabled", f"`{command_name}` is not disabled", 0xFEE75C)
        await ctx.send(embed=embed)

    # ========== 13. FAKEPERMISSIONS ==========
    @commands.command(name="fakepermissions")
    @commands.has_permissions(administrator=True)
    async def fakepermissions(self, ctx, member: discord.Member = None):
        """Show fake permission list (info only)"""
        member = member or ctx.author
        perms = [p for p, v in member.guild_permissions if v]
        embed = self.create_embed(f"🛡️ {member.display_name}'s Permissions", 
                                  "\n".join([f"✅ {p}" for p in perms[:25]]) if perms else "None",
                                  0x2b2d31, footer=f"Total: {len(perms)}")
        await ctx.send(embed=embed)

    # ========== 14. LISTPERMISSIONS ==========
    @commands.command(name="listpermissions")
    @commands.has_permissions(administrator=True)
    async def listpermissions(self, ctx, role: discord.Role = None):
        """List all permissions for a role"""
        target = role or ctx.author
        perms = target.permissions if role else target.guild_permissions
        perms_list = [p for p, v in perms if v]
        embed = self.create_embed(f"📋 Permissions for {target.name}", 
                                  "\n".join([f"✅ {p}" for p in perms_list[:25]]) if perms_list else "None",
                                  0x2b2d31, footer=f"Total: {len(perms_list)}")
        await ctx.send(embed=embed)

    # ========== 15. NUKE ==========
    @commands.command(name="nuke")
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """Delete and recreate a channel (clears all messages)"""
        channel = channel or ctx.channel
        
        embed = self.create_embed("⚠️ Confirmation", f"Nuke {channel.mention}? Reply `yes`", 0xFEE75C)
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"
        
        try:
            await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("❌ Cancelled", "Nuke cancelled", 0xED4245))
            return
        
        new_channel = await channel.clone()
        await channel.delete()
        embed = self.create_embed("💥 Channel Nuked", f"{new_channel.mention} has been nuked", 0xED4245)
        await new_channel.send(embed=embed)

    # ========== 16. REACTION-SETUP ==========
    @commands.command(name="reaction-setup")
    @commands.has_permissions(administrator=True)
    async def reaction_setup(self, ctx, message_id: int, emoji: str, role: discord.Role):
        """Setup reaction role"""
        settings = db.get_guild_settings(ctx.guild.id)
        rr_data = settings.get("reaction_roles", {})
        
        try:
            message = await ctx.channel.fetch_message(message_id)
            if str(message_id) not in rr_data:
                rr_data[str(message_id)] = {}
            rr_data[str(message_id)][emoji] = role.id
            db.update_guild_settings(ctx.guild.id, "reaction_roles", rr_data)
            await message.add_reaction(emoji)
            embed = self.create_embed("✅ Reaction Role Setup", f"{emoji} → {role.mention}", 0x57F287)
        except discord.NotFound:
            embed = self.create_embed("❌ Message Not Found", f"Message ID `{message_id}` not found", 0xED4245)
        except Exception as e:
            embed = self.create_embed("❌ Error", str(e), 0xED4245)
        await ctx.send(embed=embed)

    # ========== 17. REACTIONROLES ==========
    @commands.command(name="reactionroles")
    @commands.has_permissions(administrator=True)
    async def reactionroles(self, ctx, action: str = None, message_id: int = None):
        """List or clear reaction roles"""
        settings = db.get_guild_settings(ctx.guild.id)
        rr_data = settings.get("reaction_roles", {})
        
        if action == "clear" and message_id:
            if str(message_id) in rr_data:
                del rr_data[str(message_id)]
                db.update_guild_settings(ctx.guild.id, "reaction_roles", rr_data)
                embed = self.create_embed("✅ Reaction Roles Cleared", f"Cleared for message ID `{message_id}`", 0x57F287)
            else:
                embed = self.create_embed("❌ Not Found", f"No reaction roles for message ID `{message_id}`", 0xED4245)
        else:
            if not rr_data:
                embed = self.create_embed("📋 Reaction Roles", "No reaction roles set up.", 0xFEE75C)
            else:
                text = "\n".join([f"Message `{mid}`: {len(emojis)} reactions" for mid, emojis in rr_data.items()])
                embed = self.create_embed("📋 Reaction Roles", text[:4000], 0x2b2d31, footer=f"Total: {len(rr_data)}")
        await ctx.send(embed=embed)

    # ========== 18. SERVERRULES ==========
    @commands.command(name="serverrules")
    @commands.has_permissions(administrator=True)
    async def serverrules(self, ctx, *, rules: str = None):
        """Set or show server rules"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        
        if rules:
            current["rules"] = rules
            db.update_guild_settings(ctx.guild.id, "settings", current)
            embed = self.create_embed("📜 Server Rules Set", rules[:2000], 0x57F287)
        else:
            rules_text = current.get("rules", "No rules set. Use `!serverrules <rules>` to set them.")
            embed = self.create_embed("📜 Server Rules", rules_text[:4000], 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 19. SETTINGS ==========
    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """View current server settings"""
        settings = db.get_guild_settings(ctx.guild.id)
        s = settings.get("settings", {})
        
        embed = self.create_embed("⚙️ Server Settings", "", 0x2b2d31, fields=[
            ("🤖 Auto-Responders", str(len(settings.get("auto_responders", {}))), True),
            ("🎭 Reaction Roles", str(len(settings.get("reaction_roles", {}))), True),
            ("🔧 Disabled Commands", str(len(settings.get("disabled_commands", []))), True),
            ("🛡️ Anti-Nuke", "Enabled" if s.get("antinuke") else "Disabled", True),
            ("🛡️ Anti-Raid", "Enabled" if s.get("antiraid") else "Disabled", True),
            ("📜 Rules", "Set" if s.get("rules") else "Not set", True)
        ])
        await ctx.send(embed=embed)

    # ========== 20. STATUS ==========
    @commands.command(name="status")
    @commands.has_permissions(administrator=True)
    async def status(self, ctx, status_type: str = None):
        """Set bot status (online, idle, dnd, invisible)"""
        if not status_type:
            embed = self.create_embed("ℹ️ Status", f"Current: {self.bot.status}", 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible
        }
        
        if status_type.lower() in status_map:
            await self.bot.change_presence(status=status_map[status_type.lower()])
            embed = self.create_embed("✅ Status Updated", f"Bot status changed to {status_type}", 0x57F287)
        else:
            embed = self.create_embed("❌ Invalid Status", "Use: online, idle, dnd, invisible", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 21. STICKYMESSAGE ==========
    @commands.command(name="stickymessage")
    @commands.has_permissions(administrator=True)
    async def stickymessage(self, ctx, action: str, *, message: str = None):
        """Set a sticky message that stays at the bottom"""
        settings = db.get_guild_settings(ctx.guild.id)
        sticky = settings.get("sticky_messages", {})
        
        if action.lower() == "set" and message:
            sticky_msg = await ctx.send(embed=self.create_embed("📌 Sticky Message", message, 0x2b2d31))
            sticky[str(ctx.channel.id)] = sticky_msg.id
            db.update_guild_settings(ctx.guild.id, "sticky_messages", sticky)
            embed = self.create_embed("✅ Sticky Message Set", f"[Click here]({sticky_msg.jump_url})", 0x57F287)
        elif action.lower() == "remove":
            if str(ctx.channel.id) in sticky:
                del sticky[str(ctx.channel.id)]
                db.update_guild_settings(ctx.guild.id, "sticky_messages", sticky)
                embed = self.create_embed("✅ Sticky Message Removed", "Removed", 0x57F287)
            else:
                embed = self.create_embed("❌ No Sticky Message", "None set in this channel", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `set` or `remove`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 22. STRIPSTAFF ==========
    @commands.command(name="stripstaff")
    @commands.has_permissions(administrator=True)
    async def stripstaff(self, ctx, member: discord.Member):
        """Remove all staff/administrative roles"""
        staff_keywords = ["admin", "mod", "staff", "manager", "owner", "team"]
        removed = []
        
        for role in member.roles[:]:
            if any(k in role.name.lower() for k in staff_keywords) or role.permissions.administrator:
                await member.remove_roles(role)
                removed.append(role.name)
        
        if removed:
            embed = self.create_embed("👔 Staff Roles Removed", f"Removed from {member.mention}: {', '.join(removed)}", 0xED4245)
        else:
            embed = self.create_embed("ℹ️ No Staff Roles", f"{member.mention} has no staff roles", 0xFEE75C)
        await ctx.send(embed=embed)

    # ========== 23. UNBANNALL ==========
    @commands.command(name="unbannall")
    @commands.has_permissions(administrator=True)
    async def unbannall(self, ctx):
        """Unban all banned users"""
        embed = self.create_embed("⚠️ Confirmation", "Unban ALL banned users? Reply `yes`", 0xFEE75C)
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"
        
        try:
            await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("❌ Cancelled", "Unbann all cancelled", 0xED4245))
            return
        
        bans = [entry async for entry in ctx.guild.bans()]
        success = 0
        for entry in bans:
            try:
                await ctx.guild.unban(entry.user)
                success += 1
                await asyncio.sleep(0.5)
            except:
                pass
        
        embed = self.create_embed("✅ Unbanned All", f"Unbanned **{success}** users", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 24. UNJAIALL ==========
    @commands.command(name="unjaiall")
    @commands.has_permissions(administrator=True)
    async def unjaiall(self, ctx):
        """Remove jail role from all members"""
        role_id = db.get_jail_role(ctx.guild.id)
        if not role_id:
            embed = self.create_embed("❌ No Jail Role", "No jail role configured", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        jail_role = ctx.guild.get_role(int(role_id))
        if not jail_role:
            embed = self.create_embed("❌ Jail Role Not Found", "Please reconfigure", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        count = 0
        for member in ctx.guild.members:
            if jail_role in member.roles:
                await member.remove_roles(jail_role)
                db.remove_jailed_user(ctx.guild.id, member.id)
                count += 1
                await asyncio.sleep(0.5)
        
        embed = self.create_embed("🔓 Unjailed All", f"Removed jail role from **{count}** members", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 25. VANITY-URL ==========
    @commands.command(name="vanity-url")
    @commands.has_permissions(administrator=True)
    async def vanity_url(self, ctx):
        """Show server vanity URL"""
        if ctx.guild.vanity_url_code:
            embed = self.create_embed("✨ Vanity URL", f"discord.gg/{ctx.guild.vanity_url_code}", 0x57F287,
                                      footer=f"Uses: {ctx.guild.vanity_url_uses if ctx.guild.vanity_url_uses else 0}")
        else:
            embed = self.create_embed("❌ No Vanity URL", "Requires Boost Level 3", 0xFEE75C)
        await ctx.send(embed=embed)

    # ========== 26. VERWARNUNG ==========
    @commands.command(name="verwarnung")
    @commands.has_permissions(kick_members=True)
    async def verwarnung(self, ctx, member: discord.Member, *, grund: str = "Kein Grund"):
        """Warn a member (German warning system)"""
        db.add_warning(ctx.guild.id, member.id, grund, str(ctx.author))
        warns = db.get_warnings(ctx.guild.id, member.id)
        embed = self.create_embed("⚠️ Verwarnung", f"{member.mention} wurde verwarnt", 0xFEE75C,
                                  fields=[("📝 Grund", grund, False), ("👮 Moderator", ctx.author.mention, True), ("⚠️ Anzahl", str(len(warns)), True)])
        await ctx.send(embed=embed)

    # ========== 27. CREED (nicht implementiert) ==========
    # (Command übersprungen laut Vorgabe)

    # ========== EVENT HANDLERS ==========
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        settings = db.get_guild_settings(message.guild.id)
        responders = settings.get("auto_responders", {})
        
        for trigger, response in responders.items():
            if trigger.lower() in message.content.lower():
                await message.channel.send(response)
                break

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        
        settings = db.get_guild_settings(payload.guild_id)
        rr_data = settings.get("reaction_roles", {})
        
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
        settings = db.get_guild_settings(payload.guild_id)
        rr_data = settings.get("reaction_roles", {})
        
        if str(payload.message_id) in rr_data:
            emoji = str(payload.emoji)
            if emoji in rr_data[str(payload.message_id)]:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(rr_data[str(payload.message_id)][emoji])
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(Admin(bot))
