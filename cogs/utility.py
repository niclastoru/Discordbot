import discord
from discord.ext import commands
import base64
import asyncio


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}

    # ================= SERVER INFO =================
    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx):
        guild = ctx.guild

        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=False
        )

        embed.add_field(
            name="👥 Members",
            value=f"{guild.member_count} total\n{humans} humans | {bots} bots",
            inline=False
        )

        embed.add_field(
            name="📂 Channels",
            value=f"{len(guild.text_channels)} Text\n{len(guild.voice_channels)} Voice",
            inline=False
        )

        embed.add_field(
            name="📊 Stats",
            value=f"{len(guild.roles)} Roles\n{len(guild.emojis)} Emojis",
            inline=False
        )

        embed.set_footer(text=f"Guild ID: {guild.id}")

        await ctx.send(embed=embed)

    # ================= AVATAR =================
    @commands.command(aliases=["av"])
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"Avatar of {member}",
            color=discord.Color.blurple()
        )

        embed.set_image(url=member.display_avatar.url)

        await ctx.send(embed=embed)

    # ================= BANNER =================
    @commands.command()
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)

        if user.banner:
            embed = discord.Embed(
                title=f"Banner of {member}",
                color=discord.Color.blurple()
            )
            embed.set_image(url=user.banner.url)
        else:
            embed = discord.Embed(
                title="❌ No Banner",
                description=f"{member} has no banner",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    # ================= USER INFO =================
    @commands.command(aliases=["ui"])
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=str(member),
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="Created", value=member.created_at.strftime("%d.%m.%Y"), inline=True)

        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        embed.add_field(
            name=f"Roles [{len(roles)}]",
            value=" ".join(roles[:10]) if roles else "None",
            inline=False
        )

        await ctx.send(embed=embed)

    # ================= SNIPE =================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        self.snipes[message.channel.id] = message

    @commands.command()
    async def snipe(self, ctx):
        msg = self.snipes.get(ctx.channel.id)

        if not msg:
            return await ctx.send("❌ Nothing to snipe")

        embed = discord.Embed(
            description=msg.content or "*No text*",
            color=discord.Color.blurple()
        )

        embed.set_footer(text=f"{msg.author}")

        await ctx.send(embed=embed)

    # ================= CLEAR SNIPE =================
    @commands.command()
    async def clearsnipe(self, ctx):
        self.snipes.pop(ctx.channel.id, None)
        await ctx.send("🧹 Snipe cleared")

    # ================= BASE64 =================
    @commands.command()
    async def base64(self, ctx, *, text):
        encoded = base64.b64encode(text.encode()).decode()
        await ctx.send(encoded)

    # ================= REMIND =================
    @commands.command()
    async def remind(self, ctx, seconds: int, *, text):
        await ctx.send(f"⏰ Reminder set for {seconds}s")

        await asyncio.sleep(seconds)

        await ctx.send(f"🔔 {ctx.author.mention} {text}")

    # ================= MEMBERCOUNT =================
    @commands.command()
    async def membercount(self, ctx):
        await ctx.send(f"👥 {ctx.guild.member_count} members")

    # ================= VC =================
    @commands.command()
    async def vc(self, ctx):
        if ctx.author.voice:
            await ctx.send(f"🎤 {ctx.author.voice.channel.name}")
        else:
            await ctx.send("❌ Not in a voice channel")


async def setup(bot):
    await bot.add_cog(Utility(bot))
