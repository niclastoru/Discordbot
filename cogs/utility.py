import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3
import aiohttp
import base64
import asyncio
import json

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "utility.db"
        self.snipes = {}  # {guild_id: {channel_id: {"author": "", "content": "", "timestamp": ""}}}
        self.init_database()
        self.start_reminder_checker()

    def init_database(self):
        """Initializes database for reminders"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Table for reminders
        c.execute('''CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            guild_id TEXT,
            channel_id TEXT,
            message TEXT,
            remind_time TEXT
        )''')
        
        conn.commit()
        conn.close()

    def add_reminder(self, user_id, guild_id, channel_id, message, remind_time):
        """Adds a reminder to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO reminders (user_id, guild_id, channel_id, message, remind_time) VALUES (?, ?, ?, ?, ?)",
                  (str(user_id), str(guild_id), str(channel_id), message, remind_time))
        conn.commit()
        conn.close()

    def get_reminders(self, user_id=None):
        """Gets reminders from database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if user_id:
            c.execute("SELECT id, message, remind_time FROM reminders WHERE user_id = ? ORDER BY remind_time", (str(user_id),))
        else:
            c.execute("SELECT id, user_id, guild_id, channel_id, message, remind_time FROM reminders ORDER BY remind_time")
        result = c.fetchall()
        conn.close()
        return result

    def delete_reminder(self, reminder_id):
        """Deletes a reminder from database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()

    def start_reminder_checker(self):
        """Starts background task to check reminders"""
        async def check_reminders():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reminders = self.get_reminders()
                
                for reminder in reminders:
                    rid, user_id, guild_id, channel_id, message, remind_time = reminder
                    if remind_time <= now:
                        guild = self.bot.get_guild(int(guild_id))
                        if guild:
                            channel = guild.get_channel(int(channel_id))
                            if channel:
                                user = guild.get_member(int(user_id))
                                if user:
                                    embed = discord.Embed(title="⏰ Reminder", description=message, color=discord.Color.blue(), timestamp=datetime.now())
                                    embed.set_footer(text=f"Requested by {user.display_name}")
                                    await channel.send(f"{user.mention}", embed=embed)
                        self.delete_reminder(rid)
                
                await asyncio.sleep(30)
        
        self.bot.loop.create_task(check_reminders())

    # ========== USERAVATAR ==========
    @commands.command(aliases=["avatar", "av"])
    async def useravatar(self, ctx, member: discord.Member = None):
        """Shows a user's avatar"""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    # ========== BASE64 ==========
    @commands.command()
    async def base64(self, ctx, mode, *, text):
        """Encode or decode base64. Usage: !base64 encode <text> | !base64 decode <text>"""
        try:
            if mode.lower() == "encode":
                encoded = base64.b64encode(text.encode()).decode()
                embed = discord.Embed(title="🔐 Base64 Encode", description=f"```{encoded}```", color=discord.Color.green())
                await ctx.send(embed=embed)
            elif mode.lower() == "decode":
                decoded = base64.b64decode(text).decode()
                embed = discord.Embed(title="🔓 Base64 Decode", description=f"```{decoded}```", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Usage: `!base64 encode <text>` or `!base64 decode <text>`")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    # ========== BOOSTERS ==========
    @commands.command()
    async def boosters(self, ctx):
        """Shows all server boosters"""
        boosters = [member for member in ctx.guild.members if member.premium_since]
        
        if not boosters:
            await ctx.send("❌ This server has no boosters.")
            return
        
        booster_list = "\n".join([f"⭐ {member.mention} - Since {member.premium_since.strftime('%d.%m.%Y')}" for member in boosters])
        embed = discord.Embed(title=f"🚀 Server Boosters ({len(boosters)})", description=booster_list, color=discord.Color.purple())
        await ctx.send(embed=embed)

    # ========== CHAT ==========
    @commands.command()
    async def chat(self, ctx, *, message):
        """Simulates a webhook message as the bot"""
        if not ctx.author.guild_permissions.manage_webhooks:
            await ctx.send("❌ You need `Manage Webhooks` permission.")
            return
        
        await ctx.message.delete()
        webhooks = await ctx.channel.webhooks()
        webhook = discord.utils.get(webhooks, name="ChatBot")
        
        if not webhook:
            webhook = await ctx.channel.create_webhook(name="ChatBot")
        
        await webhook.send(content=message, username=ctx.author.display_name, avatar_url=ctx.author.avatar.url)

    # ========== CHATGPT ==========
    @commands.command()
    async def chatgpt(self, ctx, *, prompt):
        """Ask ChatGPT (requires API key)"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await ctx.send("❌ OpenAI API key not configured.")
            return
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500}
            
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    reply = result["choices"][0]["message"]["content"]
                    
                    embed = discord.Embed(title="🤖 ChatGPT", description=reply[:2000], color=discord.Color.green())
                    embed.set_footer(text=f"Prompt by {ctx.author.display_name}")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ API Error: {resp.status}")

    # ========== CLEARSNIPE ==========
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearsnipe(self, ctx, channel: discord.TextChannel = None):
        """Clears sniped messages in a channel"""
        channel = channel or ctx.channel
        if ctx.guild.id in self.snipes:
            if channel.id in self.snipes[ctx.guild.id]:
                del self.snipes[ctx.guild.id][channel.id]
        await ctx.send(f"✅ Cleared snipe data in {channel.mention}")

    # ========== DUMP ==========
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def dump(self, ctx, channel: discord.TextChannel = None):
        """Dumps recent messages from a channel (Admin only)"""
        channel = channel or ctx.channel
        messages = []
        async for msg in channel.history(limit=50):
            messages.append(f"{msg.author.name}: {msg.content}")
        
        content = "\n".join(messages)
        if len(content) > 1900:
            content = content[:1900] + "..."
        
        embed = discord.Embed(title=f"📄 Message Dump from #{channel.name}", description=f"```{content}```", color=discord.Color.orange())
        await ctx.send(embed=embed)

    # ========== EMBED ==========
    @commands.command()
    @commands.has_permissions(embed_links=True)
    async def embed(self, ctx, title, *, description):
        """Creates a custom embed. Usage: !embed "Title" Description text"""
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    # ========== GUILDBANNER ==========
    @commands.command()
    async def guildbanner(self, ctx):
        """Shows the server banner"""
        if ctx.guild.banner:
            embed = discord.Embed(title=f"{ctx.guild.name} Banner", color=discord.Color.blue())
            embed.set_image(url=ctx.guild.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ This server has no banner.")

    # ========== GUILDICON ==========
    @commands.command(aliases=["guildicon", "servericon"])
    async def guildicon(self, ctx):
        """Shows the server icon"""
        if ctx.guild.icon:
            embed = discord.Embed(title=f"{ctx.guild.name} Icon", color=discord.Color.blue())
            embed.set_image(url=ctx.guild.icon.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ This server has no icon.")

    # ========== GUILDSPLASH ==========
    @commands.command()
    async def guildsplash(self, ctx):
        """Shows the server splash/invite background"""
        if ctx.guild.splash:
            embed = discord.Embed(title=f"{ctx.guild.name} Splash", color=discord.Color.blue())
            embed.set_image(url=ctx.guild.splash.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ This server has no splash image.")

    # ========== HELP ==========
    @commands.command()
    async def help(self, ctx, command_name: str = None):
        """Shows all commands or info about a specific command"""
        if command_name:
            command = self.bot.get_command(command_name.lower())
            if command:
                embed = discord.Embed(title=f"📖 Help: {command.name}", description=command.help or "No description available.", color=discord.Color.blue())
                embed.add_field(name="Usage", value=f"`!{command.name} {command.signature}`" if command.signature else f"`!{command.name}`", inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Command `{command_name}` not found.")
            return
        
        # List all utility commands
        commands_list = [
            "useravatar", "base64", "boosters", "chat", "chatgpt", "clearsnipe",
            "dump", "embed", "guildbanner", "guildicon", "guildsplash", "help",
            "membercount", "remind", "reminders", "screenshot", "sav", "banner",
            "serverinfo", "snipe", "stealemoji", "userbanner", "userinfo", "vc"
        ]
        
        embed = discord.Embed(title="🛠️ Utility Commands", description="Here are all available utility commands:", color=discord.Color.blue())
        
        # Split into two columns
        half = len(commands_list) // 2
        embed.add_field(name="Commands (1/2)", value="\n".join([f"`!{cmd}`" for cmd in commands_list[:half]]), inline=True)
        embed.add_field(name="Commands (2/2)", value="\n".join([f"`!{cmd}`" for cmd in commands_list[half:]]), inline=True)
        embed.set_footer(text="Use !help <command> for more details")
        
        await ctx.send(embed=embed)

    # ========== MEMBERCOUNT ==========
    @commands.command()
    async def membercount(self, ctx):
        """Shows member count of the server"""
        total = ctx.guild.member_count
        humans = len([m for m in ctx.guild.members if not m.bot])
        bots = total - humans
        
        embed = discord.Embed(title=f"👥 Member Count - {ctx.guild.name}", color=discord.Color.blue())
        embed.add_field(name="Total Members", value=total, inline=True)
        embed.add_field(name="Humans", value=humans, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        await ctx.send(embed=embed)

    # ========== REMIND ==========
    @commands.command()
    async def remind(self, ctx, time, *, reminder):
        """Sets a reminder. Time format: 30s, 10m, 2h, 1d"""
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            value = int(time[:-1])
            unit = time[-1].lower()
            if unit not in units:
                await ctx.send("❌ Invalid time format. Use: 30s, 10m, 2h, 1d")
                return
            
            seconds = value * units[unit]
            remind_time = datetime.now() + timedelta(seconds=seconds)
            remind_time_str = remind_time.strftime("%Y-%m-%d %H:%M:%S")
            
            self.add_reminder(ctx.author.id, ctx.guild.id, ctx.channel.id, reminder, remind_time_str)
            
            embed = discord.Embed(title="⏰ Reminder Set", description=f"I'll remind you in {time}: {reminder}", color=discord.Color.green())
            embed.set_footer(text=f"Reminder ID: Check with !reminders")
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("❌ Invalid time format. Use: 30s, 10m, 2h, 1d")

    # ========== REMINDERS ==========
    @commands.command()
    async def reminders(self, ctx):
        """Shows your active reminders"""
        reminders = self.get_reminders(ctx.author.id)
        
        if not reminders:
            await ctx.send("📭 You have no active reminders.")
            return
        
        embed = discord.Embed(title=f"⏰ Your Reminders ({len(reminders)})", color=discord.Color.blue())
        for rid, message, remind_time in reminders[:10]:
            embed.add_field(name=f"ID: {rid}", value=f"📝 {message}\n🕐 {remind_time}", inline=False)
        
        await ctx.send(embed=embed)

    # ========== SCREENSHOT ==========
    @commands.command()
    async def screenshot(self, ctx, url):
        """Takes a screenshot of a website"""
        if not url.startswith("http"):
            url = "https://" + url
        
        api_url = f"https://image.thum.io/get/width/1200/crop/800/{url}"
        
        embed = discord.Embed(title=f"📸 Screenshot of {url}", color=discord.Color.blue())
        embed.set_image(url=api_url)
        embed.set_footer(text="Powered by thum.io")
        await ctx.send(embed=embed)

    # ========== SAV ==========
    @commands.command(aliases=["serveravatar"])
    async def sav(self, ctx):
        """Shows the server avatar (if set)"""
        if ctx.guild.icon:
            embed = discord.Embed(title=f"{ctx.guild.name} Avatar", color=discord.Color.blue())
            embed.set_image(url=ctx.guild.icon.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ This server has no avatar/icon.")

    # ========== BANNER (USER) ==========
    @commands.command(aliases=["userbanner"])
    async def banner(self, ctx, member: discord.Member = None):
        """Shows a user's banner"""
        member = member or ctx.author
        
        if not member.banner:
            # Fallback to default color or nitro banner
            await ctx.send(f"❌ {member.display_name} has no banner.")
            return
        
        embed = discord.Embed(title=f"{member.display_name}'s Banner", color=discord.Color.blue())
        embed.set_image(url=member.banner.url)
        await ctx.send(embed=embed)

    # ========== SERVERINFO ==========
    @commands.command()
    async def serverinfo(self, ctx):
        """Shows detailed server information"""
        guild = ctx.guild
        
        embed = discord.Embed(title=guild.name, description=guild.description or "No description", color=discord.Color.blue())
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="🚀 Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="⭐ Boosters", value=len([m for m in guild.members if m.premium_since]), inline=True)
        
        await ctx.send(embed=embed)

    # ========== SNIPE ==========
    @commands.command()
    async def snipe(self, ctx, channel: discord.TextChannel = None):
        """Shows the last deleted message in a channel"""
        channel = channel or ctx.channel
        
        if ctx.guild.id in self.snipes and channel.id in self.snipes[ctx.guild.id]:
            snipe_data = self.snipes[ctx.guild.id][channel.id]
            embed = discord.Embed(title="🔫 Sniped Message", description=snipe_data["content"] or "*No content*", color=discord.Color.blue(), timestamp=datetime.strptime(snipe_data["timestamp"], "%Y-%m-%d %H:%M:%S"))
            embed.set_author(name=snipe_data["author"])
            embed.set_footer(text=f"Channel: #{channel.name}")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No deleted messages found in this channel.")

    # ========== STEALEMOJI ==========
    @commands.command()
    @commands.has_permissions(manage_emojis=True)
    async def stealemoji(self, ctx, emoji: discord.PartialEmoji, *, name=None):
        """Steals an emoji from another server"""
        if not name:
            name = emoji.name
        
        if len(ctx.guild.emojis) >= ctx.guild.emoji_limit:
            await ctx.send("❌ This server has reached its emoji limit.")
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(emoji.url) as resp:
                if resp.status == 200:
                    emoji_bytes = await resp.read()
                    new_emoji = await ctx.guild.create_custom_emoji(name=name, image=emoji_bytes)
                    embed = discord.Embed(title="✅ Emoji Stolen", description=f"{new_emoji} `:{new_emoji.name}:` has been added!", color=discord.Color.green())
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Failed to steal emoji.")

    # ========== USERINFO ==========
    @commands.command(aliases=["whois", "ui"])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Shows detailed user information"""
        member = member or ctx.author
        
        embed = discord.Embed(title=f"ℹ️ User Info - {member.display_name}", color=member.color if member.color != discord.Color.default() else discord.Color.blue())
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        embed.add_field(name="📛 Name", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📅 Joined Server", value=member.joined_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="🎂 Joined Discord", value=member.created_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="🎭 Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if member.bot else "No", inline=True)
        
        # Roles list
        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        if roles:
            embed.add_field(name=f"📜 Roles ({len(roles)})", value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""), inline=False)
        
        await ctx.send(embed=embed)

    # ========== VC ==========
    @commands.command(aliases=["voice", "voicestats"])
    async def vc(self, ctx):
        """Shows who is in voice channels"""
        voice_channels = ctx.guild.voice_channels
        voice_states = []
        
        for vc in voice_channels:
            if len(vc.members) > 0:
                members = ", ".join([member.display_name for member in vc.members])
                voice_states.append(f"**{vc.name}** ({len(vc.members)}): {members}")
        
        if not voice_states:
            await ctx.send("🔇 No one is in any voice channel.")
            return
        
        embed = discord.Embed(title=f"🎤 Voice Channels - {ctx.guild.name}", description="\n\n".join(voice_states), color=discord.Color.blue())
        await ctx.send(embed=embed)

    # ========== SNIPE LISTENER ==========
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        
        if message.guild.id not in self.snipes:
            self.snipes[message.guild.id] = {}
        
        self.snipes[message.guild.id][message.channel.id] = {
            "author": f"{message.author.name}#{message.author.discriminator}",
            "content": message.content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

async def setup(bot):
    await bot.add_cog(Utility(bot))
