import discord
from discord.ext import commands
from datetime import datetime
import asyncio
from database import db

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Admin Cog geladen mit SQLite")

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

    # ========== AUTO-RESPONDER ==========

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

    # ========== REACTION ROLES ==========

    @commands.command(name="reaction-setup")
    @commands.has_permissions(administrator=True)
    async def reaction_setup(self, ctx, message_id: int, emoji: str, role: discord.Role):
        """Setup reaction role. Usage: !reaction-setup 1234567890 🎭 @Role"""
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

    @commands.command(name="reactionroles")
    @commands.has_permissions(administrator=True)
    async def reaction_roles(self, ctx, action: str = None, message_id: int = None):
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
                embed = self.create_embed("📋 Reaction Roles", text[:4000], 0x2b2d31, footer=f"Total: {len(rr_data)} messages")
        
        await ctx.send(embed=embed)

    # ========== STICKY MESSAGE ==========

    @commands.command(name="stickymessage")
    @commands.has_permissions(administrator=True)
    async def sticky_message(self, ctx, action: str, *, message: str = None):
        """Set a sticky message that stays at the bottom of the channel"""
        settings = db.get_guild_settings(ctx.guild.id)
        sticky_data = settings.get("sticky_messages", {})
        
        if action.lower() == "set":
            if not message:
                embed = self.create_embed("❌ Missing Message", "Usage: `!stickymessage set Your message here`", 0xED4245)
                await ctx.send(embed=embed)
                return
            
            sticky_msg = await ctx.send(embed=self.create_embed("📌 Sticky Message", message, 0x2b2d31))
            sticky_data[str(ctx.channel.id)] = sticky_msg.id
            db.update_guild_settings(ctx.guild.id, "sticky_messages", sticky_data)
            embed = self.create_embed("✅ Sticky Message Set", f"[Click here]({sticky_msg.jump_url})", 0x57F287)
        
        elif action.lower() == "remove":
            if str(ctx.channel.id) in sticky_data:
                del sticky_data[str(ctx.channel.id)]
                db.update_guild_settings(ctx.guild.id, "sticky_messages", sticky_data)
                embed = self.create_embed("✅ Sticky Message Removed", "The sticky message has been removed", 0x57F287)
            else:
                embed = self.create_embed("❌ No Sticky Message", "No sticky message set in this channel", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `set` or `remove`", 0xED4245)
        
        await ctx.send(embed=embed)

    # ========== DISABLE/ENABLE COMMANDS ==========

    @commands.command(name="disablecommand")
    @commands.has_permissions(administrator=True)
    async def disable_command(self, ctx, *, command_name: str):
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

    @commands.command(name="enablecommand")
    @commands.has_permissions(administrator=True)
    async def enable_command(self, ctx, *, command_name: str):
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

    # ========== ANTI-NUKE / ANTI-RAID ==========

    @commands.command(name="antinuke")
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx, mode: str = None):
        """Enable/disable anti-nuke protection"""
        if mode is None:
            status = db.get_antinuke(ctx.guild.id)
            embed = self.create_embed("🛡️ Anti-Nuke", f"Currently **{'enabled' if status else 'disabled'}**", 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        if mode.lower() == "on":
            db.set_antinuke(ctx.guild.id, True)
            embed = self.create_embed("🛡️ Anti-Nuke Enabled", "Server is now protected against nuke attacks", 0x57F287)
        elif mode.lower() == "off":
            db.set_antinuke(ctx.guild.id, False)
            embed = self.create_embed("🛡️ Anti-Nuke Disabled", "Server protection turned off", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Mode", "Use `on` or `off`", 0xED4245)
        await ctx.send(embed=embed)

    @commands.command(name="antiraid")
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, mode: str = None):
        """Enable/disable anti-raid protection"""
        if mode is None:
            status = db.get_antiraid(ctx.guild.id)
            embed = self.create_embed("🛡️ Anti-Raid", f"Currently **{'enabled' if status else 'disabled'}**", 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        if mode.lower() == "on":
            db.set_antiraid(ctx.guild.id, True)
            embed = self.create_embed("🛡️ Anti-Raid Enabled", "Server is now protected against raids", 0x57F287)
        elif mode.lower() == "off":
            db.set_antiraid(ctx.guild.id, False)
            embed = self.create_embed("🛡️ Anti-Raid Disabled", "Server protection turned off", 0xFEE75C)
        else:
            embed = self.create_embed("❌ Invalid Mode", "Use `on` or `off`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== SERVER RULES ==========

    @commands.command(name="serverrules")
    @commands.has_permissions(administrator=True)
    async def server_rules(self, ctx, *, rules: str = None):
        """Set or show server rules"""
        settings = db.get_guild_settings(ctx.guild.id)
        current_settings = settings.get("settings", {})
        
        if rules:
            current_settings["rules"] = rules
            db.update_guild_settings(ctx.guild.id, "settings", current_settings)
            embed = self.create_embed("📜 Server Rules Set", rules[:2000], 0x57F287)
        else:
            rules_text = current_settings.get("rules", "No rules set. Use `!serverrules <rules>` to set them.")
            embed = self.create_embed("📜 Server Rules", rules_text[:4000], 0x2b2d31)
        
        await ctx.send(embed=embed)

    # ========== SETTINGS ==========

    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def view_settings(self, ctx):
        """View current server settings"""
        settings = db.get_guild_settings(ctx.guild.id)
        
        embed = self.create_embed(
            "⚙️ Server Settings",
            "",
            0x2b2d31,
            fields=[
                ("🤖 Auto-Responders", str(len(settings.get("auto_responders", {}))), True),
                ("🎭 Reaction Roles", str(len(settings.get("reaction_roles", {}))), True),
                ("🔧 Disabled Commands", str(len(settings.get("disabled_commands", []))), True),
                ("📌 Sticky Messages", str(len(settings.get("sticky_messages", {}))), True),
                ("🛡️ Anti-Nuke", "Enabled" if db.get_antinuke(ctx.guild.id) else "Disabled", True),
                ("🛡️ Anti-Raid", "Enabled" if db.get_antiraid(ctx.guild.id) else "Disabled", True)
            ]
        )
        await ctx.send(embed=embed)

    # ========== NUKE ==========

    @commands.command(name="nuke")
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """Delete and recreate a channel (clears all messages)"""
        channel = channel or ctx.channel
        
        embed = self.create_embed(
            "⚠️ Confirmation",
            f"Are you sure you want to nuke {channel.mention}?\nReply with `yes` to confirm.",
            0xFEE75C
        )
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
        
        embed = self.create_embed(
            "💥 Channel Nuked",
            f"{new_channel.mention} has been nuked by {ctx.author.mention}",
            0xED4245
        )
        await new_channel.send(embed=embed)

    # ========== DM ALL ==========

    @commands.command(name="dmall")
    @commands.has_permissions(administrator=True)
    async def dm_all(self, ctx, *, message: str):
        """DM all members in the server (use with caution)"""
        embed = self.create_embed(
            "⚠️ Confirmation",
            f"Are you sure you want to DM **{len(ctx.guild.members)}** members?\nReply with `yes` to confirm.",
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
                await asyncio.sleep(1)
        
        embed = self.create_embed(
            "📬 DM All Complete",
            f"✅ Success: {success}\n❌ Failed: {failed}",
            0x57F287
        )
        await ctx.send(embed=embed)

    # ========== UNBAN ALL ==========

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
