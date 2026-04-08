import discord
from discord.ext import commands
from datetime import datetime
from database import db

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Logs Cog geladen")

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

    # ========== 1. LOGS-SETUP ==========
    @commands.command(name="logs-setup")
    @commands.has_permissions(administrator=True)
    async def logs_setup(self, ctx, action: str = None, channel: discord.TextChannel = None):
        """Setup log channels. Usage: !logs-setup mod #channel or !logs-setup message #channel"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        log_channels = current.get("log_channels", {})
        
        if action is None:
            embed = self.create_embed(
                "📋 Logs Setup",
                "**Available actions:**\n"
                "`!logs-setup mod #channel` - Set moderation log channel\n"
                "`!logs-setup message #channel` - Set message log channel\n"
                "`!logs-setup join #channel` - Set join/leave log channel\n"
                "`!logs-setup voice #channel` - Set voice log channel\n"
                "`!logs-setup remove <type>` - Remove a log channel\n"
                "`!logs-setup view` - View current log channels",
                0x2b2d31
            )
            await ctx.send(embed=embed)
            return
        
        if action.lower() == "view":
            if not log_channels:
                embed = self.create_embed("📋 Log Channels", "No log channels configured.", 0xFEE75C)
            else:
                text = ""
                for log_type, channel_id in log_channels.items():
                    ch = ctx.guild.get_channel(channel_id)
                    text += f"**{log_type}:** {ch.mention if ch else 'Deleted'}\n"
                embed = self.create_embed("📋 Log Channels", text, 0x2b2d31)
            await ctx.send(embed=embed)
            return
        
        if action.lower() == "remove":
            if not channel:
                embed = self.create_embed("❌ Missing Type", "Usage: `!logs-setup remove mod`", 0xED4245)
                await ctx.send(embed=embed)
                return
            
            log_type = channel.name.lower() if isinstance(channel, discord.TextChannel) else str(channel).lower()
            if log_type in log_channels:
                del log_channels[log_type]
                current["log_channels"] = log_channels
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Log Channel Removed", f"Removed {log_type} log channel", 0x57F287)
            else:
                embed = self.create_embed("❌ Not Found", f"No {log_type} log channel configured", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        # Set log channel
        if not channel:
            embed = self.create_embed("❌ Missing Channel", f"Usage: `!logs-setup {action} #channel`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        log_types = ["mod", "message", "join", "voice"]
        if action.lower() not in log_types:
            embed = self.create_embed("❌ Invalid Type", f"Use: {', '.join(log_types)}", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        log_channels[action.lower()] = channel.id
        current["log_channels"] = log_channels
        db.update_guild_settings(ctx.guild.id, "settings", current)
        
        embed = self.create_embed("✅ Log Channel Set", f"{action.title()} logs will be sent to {channel.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 2. SETUPLOG ==========
    @commands.command(name="setuplog")
    @commands.has_permissions(administrator=True)
    async def setuplog(self, ctx, log_type: str, channel: discord.TextChannel):
        """Setup a single log channel. Usage: !setuplog mod #channel"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        log_channels = current.get("log_channels", {})
        
        valid_types = ["mod", "message", "join", "voice", "moderation", "message_delete", "member_join", "voice_log"]
        
        if log_type.lower() not in valid_types:
            embed = self.create_embed("❌ Invalid Type", f"Valid types: {', '.join(valid_types)}", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        log_channels[log_type.lower()] = channel.id
        current["log_channels"] = log_channels
        db.update_guild_settings(ctx.guild.id, "settings", current)
        
        embed = self.create_embed("✅ Log Channel Set", f"`{log_type}` logs → {channel.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 3. SETUPLOGS ==========
    @commands.command(name="setuplogs")
    @commands.has_permissions(administrator=True)
    async def setuplogs(self, ctx, channel: discord.TextChannel):
        """Setup all log channels at once (mod, message, join, voice)"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        log_channels = current.get("log_channels", {})
        
        log_channels["mod"] = channel.id
        log_channels["message"] = channel.id
        log_channels["join"] = channel.id
        log_channels["voice"] = channel.id
        
        current["log_channels"] = log_channels
        db.update_guild_settings(ctx.guild.id, "settings", current)
        
        embed = self.create_embed("✅ All Log Channels Set", f"All logs will be sent to {channel.mention}\n\n**Types:**\n• Moderation logs\n• Message logs\n• Join/Leave logs\n• Voice logs", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 4. SHOWLOGS ==========
    @commands.command(name="showlogs")
    @commands.has_permissions(administrator=True)
    async def showlogs(self, ctx):
        """Show current log channel configuration"""
        settings = db.get_guild_settings(ctx.guild.id)
        log_channels = settings.get("settings", {}).get("log_channels", {})
        
        if not log_channels:
            embed = self.create_embed("📋 Log Configuration", "No log channels configured.\nUse `!logs-setup` to set up logs.", 0xFEE75C)
            await ctx.send(embed=embed)
            return
        
        fields = []
        for log_type, channel_id in log_channels.items():
            channel = ctx.guild.get_channel(channel_id)
            status = channel.mention if channel else "❌ Deleted"
            fields.append((f"📁 {log_type.title()}", status, True))
        
        embed = self.create_embed("📋 Log Configuration", "", 0x2b2d31, fields=fields, footer="Use !logs-setup to change")
        await ctx.send(embed=embed)

    # ========== EVENT HANDLERS ==========
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
        
        settings = db.get_guild_settings(message.guild.id)
        log_channels = settings.get("settings", {}).get("log_channels", {})
        
        channel_id = log_channels.get("message") or log_channels.get("mod")
        if not channel_id:
            return
        
        log_channel = message.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = self.create_embed(
            "🗑️ Message Deleted",
            f"**Channel:** {message.channel.mention}\n**Author:** {message.author.mention}\n**Content:** {message.content[:1000] if message.content else 'No text'}",
            0xED4245
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        
        settings = db.get_guild_settings(before.guild.id)
        log_channels = settings.get("settings", {}).get("log_channels", {})
        
        channel_id = log_channels.get("message") or log_channels.get("mod")
        if not channel_id:
            return
        
        log_channel = before.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = self.create_embed(
            "✏️ Message Edited",
            f"**Channel:** {before.channel.mention}\n**Author:** {before.author.mention}\n**Before:** {before.content[:500]}\n**After:** {after.content[:500]}",
            0xFEE75C
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        settings = db.get_guild_settings(member.guild.id)
        log_channels = settings.get("settings", {}).get("log_channels", {})
        
        channel_id = log_channels.get("join") or log_channels.get("mod")
        if not channel_id:
            return
        
        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = self.create_embed(
            "👋 Member Joined",
            f"{member.mention}\n**Name:** {member.name}\n**ID:** {member.id}\n**Created:** <t:{int(member.created_at.timestamp())}:R>",
            0x57F287
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        settings = db.get_guild_settings(member.guild.id)
        log_channels = settings.get("settings", {}).get("log_channels", {})
        
        channel_id = log_channels.get("join") or log_channels.get("mod")
        if not channel_id:
            return
        
        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = self.create_embed(
            "👋 Member Left",
            f"{member.mention}\n**Name:** {member.name}\n**ID:** {member.id}",
            0xED4245
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        settings = db.get_guild_settings(member.guild.id)
        log_channels = settings.get("settings", {}).get("log_channels", {})
        
        channel_id = log_channels.get("voice") or log_channels.get("mod")
        if not channel_id:
            return
        
        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        if before.channel is None and after.channel is not None:
            embed = self.create_embed("🔊 Joined Voice", f"{member.mention} joined {after.channel.mention}", 0x57F287)
        elif before.channel is not None and after.channel is None:
            embed = self.create_embed("🔊 Left Voice", f"{member.mention} left {before.channel.mention}", 0xED4245)
        elif before.channel != after.channel:
            embed = self.create_embed("🔊 Moved Voice", f"{member.mention} moved from {before.channel.mention} to {after.channel.mention}", 0xFEE75C)
        else:
            return
        
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        settings = db.get_guild_settings(guild.id)
        log_channels = settings.get("settings", {}).get("log_channels", {})
        
        channel_id = log_channels.get("mod")
        if not channel_id:
            return
        
        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = self.create_embed("🔨 Member Banned", f"{user.mention}\n**ID:** {user.id}", 0xED4245)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        settings = db.get_guild_settings(guild.id)
        log_channels = settings.get("settings", {}).get("log_channels", {})
        
        channel_id = log_channels.get("mod")
        if not channel_id:
            return
        
        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = self.create_embed("✅ Member Unbanned", f"{user.mention}\n**ID:** {user.id}", 0x57F287)
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
