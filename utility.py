import discord
from discord.ext import commands
from datetime import datetime
import aiohttp
import base64
import asyncio
import re
from database import db

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}
        print("✅ Utility Cog geladen")

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

    # ========== SNIPE SYSTEM ==========
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
        self.snipes[message.channel.id] = {
            "author": message.author,
            "content": message.content,
            "timestamp": datetime.utcnow(),
            "attachments": message.attachments
        }

    # ========== 1. USERAVATAR ==========
    @commands.command(name="useravatar")
    async def user_avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = self.create_embed(
            f"🖼️ {member.display_name}'s Avatar",
            f"[PNG]({member.avatar.url}) | [JPG]({member.avatar.url}) | [WEBP]({member.avatar.url})",
            0x2b2d31,
            footer=f"ID: {member.id}"
        )
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)

    # ========== 2. BASE64 ==========
    @commands.command(name="base64")
    async def base64_cmd(self, ctx, mode: str, *, text: str):
        mode = mode.lower()
        if mode == "encode":
            encoded = base64.b64encode(text.encode()).decode()
            embed = self.create_embed("🔐 Base64 Encode", f"`{encoded}`", 0x57F287)
        elif mode == "decode":
            try:
                decoded = base64.b64decode(text).decode()
                embed = self.create_embed("🔓 Base64 Decode", f"`{decoded}`", 0x57F287)
            except:
                embed = self.create_embed("❌ Decode Failed", "Invalid Base64 string", 0xED4245)
        else:
            embed = self.create_embed("❌ Invalid Mode", "Use `encode` or `decode`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 3. BOOSTERS ==========
    @commands.command(name="boosters")
    async def boosters(self, ctx):
        boosters = ctx.guild.premium_subscribers
        if not boosters:
            embed = self.create_embed("🎁 Server Boosters", "No boosters yet", 0xFEE75C)
        else:
            booster_list = "\n".join([f"⭐ {b.mention}" for b in boosters])
            embed = self.create_embed("🎁 Server Boosters", booster_list, 0x57F287, footer=f"Total: {len(boosters)} | Level: {ctx.guild.premium_tier}")
        await ctx.send(embed=embed)

    # ========== 4. CHAT ==========
    @commands.command(name="chat")
    async def chat(self, ctx, *, message: str):
        embed = self.create_embed("💬 Chat", message, 0x2b2d31, fields=[("👤 User", ctx.author.mention, True)])
        await ctx.send(embed=embed)

    # ========== 5. CHATGPT ==========
    @commands.command(name="chatgpt")
    async def chatgpt(self, ctx, *, prompt: str):
        embed = self.create_embed("🤖 ChatGPT", f"**Prompt:** {prompt}\n\n**Response:** Add OpenAI API key for real responses", 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 6. CLEARSNIPE ==========
    @commands.command(name="clearsnipe")
    @commands.has_permissions(manage_messages=True)
    async def clear_snipe(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if channel.id in self.snipes:
            del self.snipes[channel.id]
            embed = self.create_embed("🗑️ Snipe Cleared", f"Cleared for {channel.mention}", 0x57F287)
        else:
            embed = self.create_embed("❌ Nothing to Clear", f"No snipe data for {channel.mention}", 0xFEE75C)
        await ctx.send(embed=embed)

    # ========== 7. DUMP ==========
    @commands.command(name="dump")
    @commands.has_permissions(administrator=True)
    async def dump(self, ctx, channel: discord.TextChannel = None, limit: int = 100):
        channel = channel or ctx.channel
        messages = []
        async for msg in channel.history(limit=min(limit, 500)):
            messages.append(f"[{msg.created_at.strftime('%H:%M:%S')}] {msg.author}: {msg.content[:100]}")
        
        if not messages:
            embed = self.create_embed("📄 Message Dump", "No messages found", 0xFEE75C)
        else:
            dump_text = "\n".join(messages[-50:])
            if len(dump_text) > 4000:
                dump_text = dump_text[:4000] + "..."
            embed = self.create_embed(f"📄 Message Dump - #{channel.name}", f"```\n{dump_text}\n```", 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 8. EMBED ==========
    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed_cmd(self, ctx, title: str, *, description: str):
        embed = self.create_embed(title, description, 0x2b2d31, footer=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    # ========== 9. GUILDBANNER ==========
    @commands.command(name="guildbanner")
    async def guild_banner(self, ctx):
        if ctx.guild.banner:
            embed = self.create_embed(f"🎨 {ctx.guild.name} Banner", "", 0x2b2d31)
            embed.set_image(url=ctx.guild.banner.url)
        else:
            embed = self.create_embed("❌ No Banner", "This server doesn't have a banner", 0xFEE75C)
        await ctx.send(embed=embed)

    # ========== 10. GUILDICON ==========
    @commands.command(name="guildicon")
    async def guild_icon(self, ctx):
        if ctx.guild.icon:
            embed = self.create_embed(f"🖼️ {ctx.guild.name} Icon", "", 0x2b2d31)
            embed.set_image(url=ctx.guild.icon.url)
        else:
            embed = self.create_embed("❌ No Icon", "This server doesn't have an icon", 0xFEE75C)
        await ctx.send(embed=embed)

    # ========== 11. GUILDSPLASH ==========
    @commands.command(name="guildsplash")
    async def guild_splash(self, ctx):
        if ctx.guild.splash:
            embed = self.create_embed(f"🌊 {ctx.guild.name} Splash", "", 0x2b2d31)
            embed.set_image(url=ctx.guild.splash.url)
        else:
            embed = self.create_embed("❌ No Splash", "This server doesn't have a splash image", 0xFEE75C)
        await ctx.send(embed=embed)

    # ========== 12. MEMBERCOUNT ==========
    @commands.command(name="membercount")
    async def member_count(self, ctx):
        total = ctx.guild.member_count
        humans = len([m for m in ctx.guild.members if not m.bot])
        bots = total - humans
        embed = self.create_embed("👥 Member Count", f"**Total:** {total}\n**Humans:** {humans}\n**Bots:** {bots}", 0x2b2d31, footer=ctx.guild.name)
        await ctx.send(embed=embed)

    # ========== 13. REMIND ==========
    @commands.command(name="remind")
    async def remind(self, ctx, duration: str, *, reminder: str):
        total_seconds = 0
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        
        matches = re.findall(r'(\d+)([smhd])', duration.lower())
        if not matches:
            embed = self.create_embed("❌ Invalid Duration", "Use format like `10m`, `1h30m`, `2h`, `30s`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        for value, unit in matches:
            total_seconds += int(value) * time_units[unit]
        
        if total_seconds <= 0 or total_seconds > 604800:
            embed = self.create_embed("❌ Invalid Duration", "Duration must be between 1 second and 7 days", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        remind_time = datetime.utcnow() + timedelta(seconds=total_seconds)
        reminder_id = db.add_reminder(ctx.author.id, ctx.channel.id, reminder, remind_time)
        
        embed = self.create_embed("⏰ Reminder Set", f"I'll remind you in {duration}", 0x57F287,
                                  fields=[("📝 Reminder", reminder, False), ("⏱️ Time", f"<t:{int(remind_time.timestamp())}:R>", True)])
        await ctx.send(embed=embed)
        
        await asyncio.sleep(total_seconds)
        
        # Check if reminder still exists
        reminders = db.get_reminders(ctx.author.id)
        reminder_exists = any(r[0] == reminder_id for r in reminders)
        
        if reminder_exists:
            embed = self.create_embed("⏰ Reminder", reminder, 0x2b2d31)
            await ctx.send(embed=embed)
            db.delete_reminder(reminder_id)

    # ========== 14. REMINDERS ==========
    @commands.command(name="reminders")
    async def list_reminders(self, ctx):
        reminders = db.get_reminders(ctx.author.id)
        if not reminders:
            embed = self.create_embed("📋 Your Reminders", "No active reminders", 0xFEE75C)
        else:
            reminder_list = []
            for i, r in enumerate(reminders, 1):
                remind_time = datetime.fromisoformat(r[4])
                reminder_list.append(f"**{i}.** {r[3]} - <t:{int(remind_time.timestamp())}:R>")
            embed = self.create_embed("📋 Your Reminders", "\n".join(reminder_list), 0x2b2d31, footer=f"Total: {len(reminders)}")
        await ctx.send(embed=embed)

    # ========== 15. SCREENSHOT ==========
    @commands.command(name="screenshot")
    async def screenshot(self, ctx, url: str):
        embed = self.create_embed("📸 Screenshot", f"Requested: {url}", 0x2b2d31)
        embed.set_image(url=f"https://image.thum.io/get/width/1920/crop/800/{url}")
        await ctx.send(embed=embed)

    # ========== 16. SAV ==========
    @commands.command(name="sav")
    async def server_avatar(self, ctx):
        await self.guild_icon(ctx)

    # ========== 17. BANNER ==========
    @commands.command(name="banner")
    async def user_banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = self.create_embed(f"🎨 {member.display_name}'s Banner", "Fetching banner...", 0x2b2d31)
        await ctx.send(embed=embed)

    # ========== 18. SERVERINFO ==========
    @commands.command(name="serverinfo")
    async def server_info(self, ctx):
        guild = ctx.guild
        embed = self.create_embed(f"📊 {guild.name}", "", 0x2b2d31, fields=[
            ("👑 Owner", guild.owner.mention, True),
            ("📅 Created", f"<t:{int(guild.created_at.timestamp())}:R>", True),
            ("👥 Members", str(guild.member_count), True),
            ("💬 Channels", f"{len(guild.text_channels)} text / {len(guild.voice_channels)} voice", True),
            ("🎭 Roles", str(len(guild.roles)), True),
            ("🎁 Boost Level", f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)", True),
            ("🆔 Server ID", str(guild.id), False)
        ])
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    # ========== 19. SNIPE ==========
    @commands.command(name="snipe")
    async def snipe(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        snipe_data = self.snipes.get(channel.id)
        
        if not snipe_data:
            embed = self.create_embed("🔫 Snipe", f"No deleted messages in {channel.mention}", 0xFEE75C)
        else:
            content = snipe_data["content"] if snipe_data["content"] else "*No text content*"
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            embed = self.create_embed("🔫 Snipe", content, 0x2b2d31, fields=[
                ("👤 Author", snipe_data["author"].mention, True),
                ("📅 Deleted", f"<t:{int(snipe_data['timestamp'].timestamp())}:R>", True)
            ], footer=f"Channel: #{channel.name}")
        await ctx.send(embed=embed)

    # ========== 20. STEALEMOJI ==========
    @commands.command(name="stealemoji")
    @commands.has_permissions(manage_emojis=True)
    async def steal_emoji(self, ctx, emoji: str, *, name: str = None):
        try:
            if emoji.startswith("<a:"):
                emoji_id = int(emoji.split(":")[2].split(">")[0])
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.gif"
            elif emoji.startswith("<:"):
                emoji_id = int(emoji.split(":")[2].split(">")[0])
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            else:
                embed = self.create_embed("❌ Invalid Emoji", "Please provide a custom emoji from another server", 0xED4245)
                await ctx.send(embed=embed)
                return
            
            if not name:
                name = f"stealed_{emoji_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(emoji_url) as resp:
                    if resp.status == 200:
                        emoji_bytes = await resp.read()
                        new_emoji = await ctx.guild.create_custom_emoji(name=name, image=emoji_bytes)
                        embed = self.create_embed("✅ Emoji Stolen", f"Added {new_emoji} with name `{name}`", 0x57F287)
                    else:
                        embed = self.create_embed("❌ Failed", "Could not download the emoji", 0xED4245)
        except discord.Forbidden:
            embed = self.create_embed("❌ Permission Denied", "I need `Manage Emojis` permission", 0xED4245)
        except Exception as e:
            embed = self.create_embed("❌ Error", str(e), 0xED4245)
        await ctx.send(embed=embed)

    # ========== 21. USERBANNER ==========
    @commands.command(name="userbanner")
    async def user_banner_cmd(self, ctx, member: discord.Member = None):
        await self.user_banner(ctx, member)

    # ========== 22. USERINFO ==========
    @commands.command(name="userinfo")
    async def user_info(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        roles = [r.mention for r in member.roles if r.name != "@everyone"][:10]
        roles_text = ", ".join(roles) if roles else "None"
        
        embed = self.create_embed(f"👤 {member.display_name}", "", 0x2b2d31, fields=[
            ("🆔 User ID", str(member.id), True),
            ("📅 Joined Server", f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown", True),
            ("📅 Joined Discord", f"<t:{int(member.created_at.timestamp())}:R>", True),
            ("🎭 Roles", roles_text, False),
            ("🤖 Bot", "Yes" if member.bot else "No", True),
            ("👑 Booster", f"Since <t:{int(member.premium_since.timestamp())}:R>" if member.premium_since else "No", True)
        ])
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)

    # ========== 23. VC ==========
    @commands.command(name="vc")
    async def voice_channels(self, ctx):
        voice_channels = [vc for vc in ctx.guild.voice_channels]
        if not voice_channels:
            embed = self.create_embed("🔊 Voice Channels", "No voice channels in this server", 0xFEE75C)
        else:
            vc_list = []
            for vc in voice_channels:
                member_count = len(vc.members)
                vc_list.append(f"🔊 {vc.mention} - `{member_count} members`")
            embed = self.create_embed("🔊 Voice Channels", "\n".join(vc_list), 0x2b2d31, footer=f"Total: {len(voice_channels)} channels")
        await ctx.send(embed=embed)

    # ========== 24. USERAVATAR alias ==========
    # Already have useravatar

async def setup(bot):
    await bot.add_cog(Utility(bot))
