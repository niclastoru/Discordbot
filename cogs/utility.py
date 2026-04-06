import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3
import aiohttp
import base64
import asyncio
import os

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "utility.db"
        self.snipes = {}
        self.init_database()
        self.bot.loop.create_task(self.check_reminders())

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
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
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO reminders (user_id, guild_id, channel_id, message, remind_time) VALUES (?, ?, ?, ?, ?)",
                  (str(user_id), str(guild_id), str(channel_id), message, remind_time))
        conn.commit()
        conn.close()

    def get_reminders(self, user_id=None):
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
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()

    async def check_reminders(self):
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
                                await channel.send(f"{user.mention}", embed=embed)
                    self.delete_reminder(rid)
            
            await asyncio.sleep(30)

    @commands.command()
    async def useravatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def base64(self, ctx, mode, *, text):
        try:
            if mode.lower() == "encode":
                encoded = base64.b64encode(text.encode()).decode()
                await ctx.send(f"🔐 **Encoded:** `{encoded}`")
            elif mode.lower() == "decode":
                decoded = base64.b64decode(text).decode()
                await ctx.send(f"🔓 **Decoded:** `{decoded}`")
            else:
                await ctx.send("❌ Usage: `!base64 encode <text>` or `!base64 decode <text>`")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command()
    async def boosters(self, ctx):
        boosters = [m for m in ctx.guild.members if m.premium_since]
        if not boosters:
            await ctx.send("❌ No boosters.")
            return
        booster_list = "\n".join([f"⭐ {m.mention}" for m in boosters])
        embed = discord.Embed(title=f"Boosters ({len(boosters)})", description=booster_list, color=discord.Color.purple())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_webhooks=True)
    async def chat(self, ctx, *, message):
        await ctx.message.delete()
        webhook = discord.utils.get(await ctx.channel.webhooks(), name="ChatBot")
        if not webhook:
            webhook = await ctx.channel.create_webhook(name="ChatBot")
        await webhook.send(content=message, username=ctx.author.display_name, avatar_url=ctx.author.avatar.url)

    @commands.command()
    async def chatgpt(self, ctx, *, prompt):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await ctx.send("❌ OpenAI API key not set.")
            return
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500}
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    reply = result["choices"][0]["message"]["content"]
                    await ctx.send(f"🤖 **ChatGPT:** {reply[:1900]}")
                else:
                    await ctx.send(f"❌ API Error: {resp.status}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearsnipe(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if ctx.guild.id in self.snipes and channel.id in self.snipes[ctx.guild.id]:
            del self.snipes[ctx.guild.id][channel.id]
        await ctx.send(f"✅ Cleared snipe in {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def dump(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        messages = []
        async for msg in channel.history(limit=50):
            messages.append(f"{msg.author.name}: {msg.content}")
        content = "\n".join(messages)[:1900]
        await ctx.send(f"```{content}```")

    @commands.command()
    @commands.has_permissions(embed_links=True)
    async def embed(self, ctx, title, *, description):
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def guildbanner(self, ctx):
        if ctx.guild.banner:
            embed = discord.Embed(title=f"{ctx.guild.name} Banner", color=discord.Color.blue())
            embed.set_image(url=ctx.guild.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No banner.")

    @commands.command()
    async def guildicon(self, ctx):
        if ctx.guild.icon:
            embed = discord.Embed(title=f"{ctx.guild.name} Icon", color=discord.Color.blue())
            embed.set_image(url=ctx.guild.icon.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No icon.")

    @commands.command()
    async def guildsplash(self, ctx):
        if ctx.guild.splash:
            embed = discord.Embed(title=f"{ctx.guild.name} Splash", color=discord.Color.blue())
            embed.set_image(url=ctx.guild.splash.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No splash.")

    @commands.command()
    async def help(self, ctx, command_name: str = None):
        if command_name:
            cmd = self.bot.get_command(command_name.lower())
            if cmd:
                await ctx.send(f"**!{cmd.name}** - {cmd.help or 'No description'}")
            else:
                await ctx.send(f"❌ Command `{command_name}` not found.")
            return
        
        cmds = ["useravatar", "base64", "boosters", "chat", "chatgpt", "clearsnipe", "dump", "embed", "guildbanner", "guildicon", "guildsplash", "help", "membercount", "remind", "reminders", "screenshot", "sav", "banner", "serverinfo", "snipe", "stealemoji", "userinfo", "vc"]
        embed = discord.Embed(title="Utility Commands", description="\n".join([f"`!{c}`" for c in cmds]), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def membercount(self, ctx):
        total = ctx.guild.member_count
        humans = len([m for m in ctx.guild.members if not m.bot])
        bots = total - humans
        embed = discord.Embed(title=f"Member Count", color=discord.Color.blue())
        embed.add_field(name="Total", value=total, inline=True)
        embed.add_field(name="Humans", value=humans, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def remind(self, ctx, time, *, reminder):
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            value = int(time[:-1])
            unit = time[-1].lower()
            if unit not in units:
                await ctx.send("❌ Use: 30s, 10m, 2h, 1d")
                return
            seconds = value * units[unit]
            remind_time = (datetime.now() + timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")
            self.add_reminder(ctx.author.id, ctx.guild.id, ctx.channel.id, reminder, remind_time)
            await ctx.send(f"✅ Reminder set for {time}: {reminder}")
        except:
            await ctx.send("❌ Invalid format. Use: 30s, 10m, 2h, 1d")

    @commands.command()
    async def reminders(self, ctx):
        reminders = self.get_reminders(ctx.author.id)
        if not reminders:
            await ctx.send("📭 No reminders.")
            return
        for rid, msg, time in reminders[:5]:
            await ctx.send(f"🔔 **ID {rid}:** {msg} - {time}")

    @commands.command()
    async def screenshot(self, ctx, url):
        if not url.startswith("http"):
            url = "https://" + url
        embed = discord.Embed(title=f"Screenshot", color=discord.Color.blue())
        embed.set_image(url=f"https://image.thum.io/get/width/1200/crop/800/{url}")
        await ctx.send(embed=embed)

    @commands.command()
    async def sav(self, ctx):
        if ctx.guild.icon:
            embed = discord.Embed(title=f"Server Avatar", color=discord.Color.blue())
            embed.set_image(url=ctx.guild.icon.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No server icon.")

    @commands.command()
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        if member.banner:
            embed = discord.Embed(title=f"{member.display_name}'s Banner", color=discord.Color.blue())
            embed.set_image(url=member.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {member.display_name} has no banner.")

    @commands.command()
    async def serverinfo(self, ctx):
        g = ctx.guild
        embed = discord.Embed(title=g.name, color=discord.Color.blue())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Owner", value=g.owner.mention, inline=True)
        embed.add_field(name="Members", value=g.member_count, inline=True)
        embed.add_field(name="Channels", value=len(g.channels), inline=True)
        embed.add_field(name="Roles", value=len(g.roles), inline=True)
        embed.add_field(name="Boost Level", value=g.premium_tier, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def snipe(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if ctx.guild.id in self.snipes and channel.id in self.snipes[ctx.guild.id]:
            data = self.snipes[ctx.guild.id][channel.id]
            await ctx.send(f"🔫 **{data['author']}:** {data['content']}")
        else:
            await ctx.send("❌ Nothing to snipe.")

    @commands.command()
    @commands.has_permissions(manage_emojis=True)
    async def stealemoji(self, ctx, emoji: discord.PartialEmoji, *, name=None):
        name = name or emoji.name
        async with aiohttp.ClientSession() as session:
            async with session.get(emoji.url) as resp:
                if resp.status == 200:
                    img = await resp.read()
                    new_emoji = await ctx.guild.create_custom_emoji(name=name, image=img)
                    await ctx.send(f"✅ Stolen: {new_emoji} `:{new_emoji.name}:`")
                else:
                    await ctx.send("❌ Failed.")

    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info - {member.display_name}", color=member.color or discord.Color.blue())
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Name", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="Created", value=member.created_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def vc(self, ctx):
        voice_channels = [vc for vc in ctx.guild.voice_channels if len(vc.members) > 0]
        if not voice_channels:
            await ctx.send("🔇 No one in VC.")
            return
        for vc in voice_channels:
            members = ", ".join([m.display_name for m in vc.members])
            await ctx.send(f"🎤 **{vc.name}** ({len(vc.members)}): {members}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        if message.guild.id not in self.snipes:
            self.snipes[message.guild.id] = {}
        self.snipes[message.guild.id][message.channel.id] = {
            "author": f"{message.author.name}#{message.author.discriminator}",
            "content": message.content[:500]
        }

async def setup(bot):
    await bot.add_cog(Utility(bot))
