import discord
from discord.ext import commands
import base64
import asyncio

class Utility(commands.Cog, name="Utility"):
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}
        self.reminders = {}

class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx):
        guild = ctx.guild

        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(
            name="📅 Server Created",
            value=f"<t:{int(guild.created_at.timestamp())}:F>",
            inline=False
        )

        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=False
        )

        embed.add_field(
            name="👥 Members",
            value=f"Total: {guild.member_count}\nHumans: {humans}\nBots: {bots}",
            inline=False
        )

        embed.add_field(
            name="📂 Channels",
            value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategory: {categories}",
            inline=False
        )

        embed.set_footer(text=f"{ctx.guild.id}")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
    

    # ================= USER AVATAR =================
    @commands.command()
    async def useravatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(member.display_avatar.url)

    # ================= USER BANNER =================
    @commands.command()
    async def userbanner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if user.banner:
            await ctx.send(user.banner.url)
        else:
            await ctx.send("❌ No banner")

    # ================= SERVER BANNER =================
    @commands.command()
    async def sbanner(self, ctx):
        if ctx.guild.banner:
            await ctx.send(ctx.guild.banner.url)
        else:
            await ctx.send("❌ No banner")

    # ================= GUILD ICON =================
    @commands.command()
    async def guildicon(self, ctx):
        await ctx.send(ctx.guild.icon.url if ctx.guild.icon else "❌ No icon")

    # ================= GUILD BANNER =================
    @commands.command()
    async def guildbanner(self, ctx):
        if ctx.guild.banner:
            await ctx.send(ctx.guild.banner.url)
        else:
            await ctx.send("❌ No banner")

    # ================= GUILD SPLASH =================
    @commands.command()
    async def guildsplash(self, ctx):
        if ctx.guild.splash:
            await ctx.send(ctx.guild.splash.url)
        else:
            await ctx.send("❌ No splash")

    # ================= USER INFO =================
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=str(member), color=discord.Color.blurple())
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined", value=member.joined_at)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    # ================= MEMBER COUNT =================
    @commands.command()
    async def membercount(self, ctx):
        await ctx.send(f"👥 {ctx.guild.member_count} members")

    # ================= BASE64 =================
    @commands.command()
    async def base64(self, ctx, *, text):
        encoded = base64.b64encode(text.encode()).decode()
        await ctx.send(encoded)

    # ================= CHAT =================
    @commands.command()
    async def chat(self, ctx, *, text):
        await ctx.send(text)

    # ================= CHATGPT (FAKE) =================
    @commands.command()
    async def chatgpt(self, ctx, *, text):
        await ctx.send(f"🤖 {text}")

    # ================= SNIPE =================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.snipes[message.channel.id] = message

    @commands.command()
    async def snipe(self, ctx):
        msg = self.snipes.get(ctx.channel.id)
        if not msg:
            return await ctx.send("❌ Nothing to snipe")
        await ctx.send(f"{msg.author}: {msg.content}")

    # ================= CLEARSNIPE =================
    @commands.command()
    async def clearsnipe(self, ctx):
        self.snipes.pop(ctx.channel.id, None)
        await ctx.send("🧹 Cleared snipe")

    # ================= DUMP =================
    @commands.command()
    async def dump(self, ctx):
        roles = "\n".join([r.name for r in ctx.guild.roles])
        await ctx.send(f"Roles:\n{roles}")

    # ================= BOOSTERS =================
    @commands.command()
    async def boosters(self, ctx):
        boosters = [m.mention for m in ctx.guild.premium_subscribers]
        await ctx.send("\n".join(boosters) if boosters else "No boosters")

    # ================= REMIND =================
    @commands.command()
    async def remind(self, ctx, seconds: int, *, text):
        await ctx.send(f"⏰ Reminder set for {seconds}s")

        await asyncio.sleep(seconds)
        await ctx.send(f"🔔 {ctx.author.mention} {text}")

    # ================= REMINDERS =================
    @commands.command()
    async def reminders(self, ctx):
        await ctx.send("📋 Active reminders not stored (basic system)")

    # ================= SCREENSHOT =================
    @commands.command()
    async def screenshot(self, ctx, url):
        await ctx.send(f"📸 Screenshot: {url}")

    # ================= SAV =================
    @commands.command()
    async def sav(self, ctx):
        await ctx.send(ctx.author.display_avatar.url)

    # ================= VC =================
    @commands.command()
    async def vc(self, ctx):
        if ctx.author.voice:
            await ctx.send(f"🎤 {ctx.author.voice.channel.name}")
        else:
            await ctx.send("❌ Not in VC")

    # ================= STEALEMOJI =================
    @commands.command()
    async def stealemoji(self, ctx, emoji: discord.PartialEmoji):
        new = await ctx.guild.create_custom_emoji(name=emoji.name, image=await emoji.read())
        await ctx.send(f"✅ Added {new}")

    #
# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Utility(bot))
