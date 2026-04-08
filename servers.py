import discord
from discord.ext import commands
from datetime import datetime
from database import db

class Servers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Servers Cog geladen")

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

    # ========== 1. AUTOROLE ==========
    @commands.command(name="autorole")
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx, action: str, role: discord.Role = None):
        """Auto role for new members. Usage: !autorole set @Role or !autorole remove"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        
        if action.lower() == "set":
            if not role:
                embed = self.create_embed("❌ Missing Role", "Usage: `!autorole set @Role`", 0xED4245)
            else:
                current["autorole"] = role.id
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Autorole Set", f"New members will get {role.mention}", 0x57F287)
        
        elif action.lower() == "remove":
            if "autorole" in current:
                del current["autorole"]
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Autorole Removed", "New members will no longer get a role", 0x57F287)
            else:
                embed = self.create_embed("❌ No Autorole", "No autorole configured", 0xFEE75C)
        
        elif action.lower() == "view":
            role_id = current.get("autorole")
            if role_id:
                r = ctx.guild.get_role(int(role_id))
                embed = self.create_embed("📋 Current Autorole", r.mention if r else "Role not found", 0x2b2d31)
            else:
                embed = self.create_embed("📋 Current Autorole", "Not set", 0x2b2d31)
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `set`, `remove`, or `view`", 0xED4245)
        
        await ctx.send(embed=embed)

    # ========== 2. GUILDWHITELIST ==========
    @commands.command(name="guildwhitelist")
    @commands.has_permissions(administrator=True)
    async def guildwhitelist(self, ctx, action: str, user: discord.Member = None):
        """Whitelist users to bypass certain restrictions"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        whitelist = current.get("guild_whitelist", [])
        
        if action.lower() == "add":
            if not user:
                embed = self.create_embed("❌ Missing User", "Usage: `!guildwhitelist add @user`", 0xED4245)
            elif str(user.id) in whitelist:
                embed = self.create_embed("⚠️ Already Whitelisted", f"{user.mention} is already whitelisted", 0xFEE75C)
            else:
                whitelist.append(str(user.id))
                current["guild_whitelist"] = whitelist
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ User Whitelisted", f"{user.mention} has been whitelisted", 0x57F287)
        
        elif action.lower() == "remove":
            if not user:
                embed = self.create_embed("❌ Missing User", "Usage: `!guildwhitelist remove @user`", 0xED4245)
            elif str(user.id) not in whitelist:
                embed = self.create_embed("⚠️ Not Whitelisted", f"{user.mention} is not whitelisted", 0xFEE75C)
            else:
                whitelist.remove(str(user.id))
                current["guild_whitelist"] = whitelist
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ User Removed", f"{user.mention} removed from whitelist", 0x57F287)
        
        elif action.lower() == "list":
            if not whitelist:
                embed = self.create_embed("📋 Guild Whitelist", "No users whitelisted.", 0xFEE75C)
            else:
                users = "\n".join([f"• <@{u}>" for u in whitelist])
                embed = self.create_embed("📋 Guild Whitelist", users, 0x2b2d31, footer=f"Total: {len(whitelist)}")
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add`, `remove`, or `list`", 0xED4245)
        
        await ctx.send(embed=embed)

    # ========== 3. PREFIX ==========
    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, new_prefix: str = None):
        """Set a custom prefix for this server (max 3 prefixes)"""
        settings = db.get_guild_settings(ctx.guild.id)
        prefixes = settings.get("settings", {}).get("prefixes", ["!"])
        
        if not new_prefix:
            embed = self.create_embed("📋 Current Prefixes", ", ".join(prefixes), 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        if len(prefixes) >= 3:
            embed = self.create_embed("❌ Too Many Prefixes", "Maximum 3 prefixes per server. Remove one first.", 0xED4245)
        elif new_prefix in prefixes:
            embed = self.create_embed("⚠️ Already Exists", f"`{new_prefix}` is already a prefix", 0xFEE75C)
        else:
            prefixes.append(new_prefix)
            current = settings.get("settings", {})
            current["prefixes"] = prefixes
            db.update_guild_settings(ctx.guild.id, "settings", current)
            embed = self.create_embed("✅ Prefix Added", f"Added `{new_prefix}` as a prefix", 0x57F287)
        
        await ctx.send(embed=embed)

    # ========== 4. PREFIX-REMOVE ==========
    @commands.command(name="prefix-remove")
    @commands.has_permissions(administrator=True)
    async def prefix_remove(self, ctx, prefix: str):
        """Remove a custom prefix from this server"""
        settings = db.get_guild_settings(ctx.guild.id)
        prefixes = settings.get("settings", {}).get("prefixes", ["!"])
        
        if prefix == "!":
            embed = self.create_embed("❌ Cannot Remove", "The default prefix `!` cannot be removed", 0xED4245)
        elif prefix not in prefixes:
            embed = self.create_embed("❌ Prefix Not Found", f"`{prefix}` is not a registered prefix", 0xED4245)
        else:
            prefixes.remove(prefix)
            current = settings.get("settings", {})
            current["prefixes"] = prefixes
            db.update_guild_settings(ctx.guild.id, "settings", current)
            embed = self.create_embed("✅ Prefix Removed", f"Removed `{prefix}` as a prefix", 0x57F287)
        
        await ctx.send(embed=embed)

    # ========== 5. PREFIX-VIEW ==========
    @commands.command(name="prefix-view")
    @commands.has_permissions(administrator=True)
    async def prefix_view(self, ctx):
        """View all current prefixes for this server"""
        settings = db.get_guild_settings(ctx.guild.id)
        prefixes = settings.get("settings", {}).get("prefixes", ["!"])
        
        embed = self.create_embed("📋 Server Prefixes", ", ".join(prefixes), 0x2b2d31, 
                                  footer=f"Total: {len(prefixes)} prefixes | Default: !")
        await ctx.send(embed=embed)

    # ========== 6. TICKETPANEL ==========
    @commands.command(name="ticketpanel")
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx, channel: discord.TextChannel = None):
        """Create a ticket panel in the specified channel"""
        channel = channel or ctx.channel
        
        embed = self.create_embed(
            "🎫 Support Ticket",
            "Click the button below to create a support ticket.\nA staff member will assist you shortly.",
            0x2b2d31
        )
        
        view = discord.ui.View(timeout=None)
        
        class TicketButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
            
            async def callback(self, interaction: discord.Interaction):
                # Create ticket channel
                guild = interaction.guild
                user = interaction.user
                
                # Check if user already has an open ticket
                for channel in guild.channels:
                    if channel.name == f"ticket-{user.name.lower()}":
                        await interaction.response.send_message("❌ You already have an open ticket!", ephemeral=True)
                        return
                
                # Create overwrites
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                
                # Add staff roles
                settings = db.get_guild_settings(guild.id)
                staff_roles = settings.get("settings", {}).get("staff_roles", [])
                for role_id in staff_roles:
                    role = guild.get_role(int(role_id))
                    if role:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
                ticket_channel = await guild.create_text_channel(
                    f"ticket-{user.name}",
                    overwrites=overwrites,
                    category=channel.category
                )
                
                ticket_embed = self.create_embed(
                    "🎫 Support Ticket",
                    f"Ticket created by {user.mention}\n\nPlease describe your issue. Staff will be with you shortly.",
                    0x57F287
                )
                
                close_button = discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.danger)
                
                async def close_callback(interaction2):
                    await ticket_channel.delete()
                
                close_button.callback = close_callback
                close_view = discord.ui.View()
                close_view.add_item(close_button)
                
                await ticket_channel.send(content=f"{user.mention}", embed=ticket_embed, view=close_view)
                await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)
        
        view.add_item(TicketButton())
        
        await channel.send(embed=embed, view=view)
        embed = self.create_embed("✅ Ticket Panel Created", f"Ticket panel created in {channel.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 7. VANITY-ROLE ==========
    @commands.command(name="vanity-role")
    @commands.has_permissions(administrator=True)
    async def vanity_role(self, ctx, role: discord.Role = None):
        """Set a role for users with vanity URL booster"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        
        if role:
            current["vanity_role"] = role.id
            db.update_guild_settings(ctx.guild.id, "settings", current)
            embed = self.create_embed("✅ Vanity Role Set", f"Boosters with vanity URL will get {role.mention}", 0x57F287)
        else:
            role_id = current.get("vanity_role")
            r = ctx.guild.get_role(int(role_id)) if role_id else None
            embed = self.create_embed("📋 Current Vanity Role", r.mention if r else "Not set", 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 8. WELCOME-ADD ==========
    @commands.command(name="welcome-add")
    @commands.has_permissions(administrator=True)
    async def welcome_add(self, ctx, channel: discord.TextChannel, *, message: str):
        """Add a welcome message for new members. Use {user} as placeholder"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        welcome_messages = current.get("welcome_messages", [])
        
        welcome_messages.append({
            "channel_id": channel.id,
            "message": message
        })
        current["welcome_messages"] = welcome_messages
        db.update_guild_settings(ctx.guild.id, "settings", current)
        
        embed = self.create_embed("✅ Welcome Message Added", f"In {channel.mention}\n{message[:200]}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 9. WELCOME-LIST ==========
    @commands.command(name="welcome-list")
    @commands.has_permissions(administrator=True)
    async def welcome_list(self, ctx):
        """List all welcome messages"""
        settings = db.get_guild_settings(ctx.guild.id)
        welcome_messages = settings.get("settings", {}).get("welcome_messages", [])
        
        if not welcome_messages:
            embed = self.create_embed("📋 Welcome Messages", "No welcome messages configured.\nUse `!welcome-add #channel message`", 0xFEE75C)
        else:
            msg_list = []
            for i, msg in enumerate(welcome_messages, 1):
                channel = ctx.guild.get_channel(msg["channel_id"])
                msg_list.append(f"**{i}.** {channel.mention if channel else 'Deleted channel'}\n   {msg['message'][:100]}...")
            embed = self.create_embed("📋 Welcome Messages", "\n\n".join(msg_list), 0x2b2d31, footer=f"Total: {len(welcome_messages)}")
        await ctx.send(embed=embed)

    # ========== 10. WELCOME-REMOVE ==========
    @commands.command(name="welcome-remove")
    @commands.has_permissions(administrator=True)
    async def welcome_remove(self, ctx, index: int):
        """Remove a welcome message by index number (from !welcome-list)"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        welcome_messages = current.get("welcome_messages", [])
        
        if index < 1 or index > len(welcome_messages):
            embed = self.create_embed("❌ Invalid Index", f"Use a number between 1 and {len(welcome_messages)}", 0xED4245)
        else:
            removed = welcome_messages.pop(index - 1)
            current["welcome_messages"] = welcome_messages
            db.update_guild_settings(ctx.guild.id, "settings", current)
            embed = self.create_embed("✅ Welcome Message Removed", f"Removed message #{index}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 11. WELCOME-VIEW ==========
    @commands.command(name="welcome-view")
    @commands.has_permissions(administrator=True)
    async def welcome_view(self, ctx, index: int = 1):
        """View a specific welcome message by index"""
        settings = db.get_guild_settings(ctx.guild.id)
        welcome_messages = settings.get("settings", {}).get("welcome_messages", [])
        
        if not welcome_messages:
            embed = self.create_embed("📋 Welcome Messages", "No welcome messages configured.", 0xFEE75C)
        elif index < 1 or index > len(welcome_messages):
            embed = self.create_embed("❌ Invalid Index", f"Use a number between 1 and {len(welcome_messages)}", 0xED4245)
        else:
            msg = welcome_messages[index - 1]
            channel = ctx.guild.get_channel(msg["channel_id"])
            embed = self.create_embed(f"📋 Welcome Message #{index}", 
                                       f"**Channel:** {channel.mention if channel else 'Deleted'}\n**Message:**\n{msg['message']}", 
                                       0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 12. WELCOME ==========
    @commands.command(name="welcome")
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx, action: str = None, *, args: str = None):
        """Test or toggle welcome messages. Usage: !welcome test or !welcome toggle"""
        if action == "test":
            embed = self.create_embed("🎉 Welcome Test", "This is how new members will see the welcome message", 0x57F287)
            await ctx.send(embed=embed)
        
        elif action == "toggle":
            settings = db.get_guild_settings(ctx.guild.id)
            current = settings.get("settings", {})
            current["welcome_enabled"] = not current.get("welcome_enabled", True)
            db.update_guild_settings(ctx.guild.id, "settings", current)
            status = "enabled" if current["welcome_enabled"] else "disabled"
            embed = self.create_embed("✅ Welcome Messages", f"Welcome messages are now **{status}**", 0x57F287)
            await ctx.send(embed=embed)
        
        else:
            embed = self.create_embed("📋 Welcome Command", 
                                       "**Subcommands:**\n`!welcome test` - Test welcome message\n`!welcome toggle` - Enable/disable welcome messages", 
                                       0x2b2d31)
            await ctx.send(embed=embed)

    # ========== EVENT: AUTO ROLE & WELCOME ==========
    @commands.Cog.listener()
    async def on_member_join(self, member):
        settings = db.get_guild_settings(member.guild.id)
        current = settings.get("settings", {})
        
        # Auto role
        auto_role_id = current.get("autorole")
        if auto_role_id:
            role = member.guild.get_role(int(auto_role_id))
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass
        
        # Welcome messages
        if current.get("welcome_enabled", True):
            welcome_messages = current.get("welcome_messages", [])
            for msg in welcome_messages:
                channel = member.guild.get_channel(msg["channel_id"])
                if channel:
                    welcome_text = msg["message"].replace("{user}", member.mention).replace("{server}", member.guild.name)
                    embed = self.create_embed("🎉 Welcome!", welcome_text, 0x57F287)
                    await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Servers(bot))
