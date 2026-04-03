import discord
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= AVATAR =================
    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"{member.name}'s Avatar",
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
                title=f"{member.name}'s Banner",
                color=discord.Color.blurple()
            )
            embed.set_image(url=user.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ This user has no banner")

    # ================= USER INFO =================
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"{member}",
            color=discord.Color.blurple()
        )

        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%d.%m.%Y"))
        embed.add_field(name="Created", value=member.created_at.strftime("%d.%m.%Y"))
        embed.add_field(name="Top Role", value=member.top_role.mention)

        await ctx.send(embed=embed)

    # ================= SERVER INFO =================
    @commands.command()
    async def serverinfo(self, ctx):
        guild = ctx.guild

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple()
        )

        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Created", value=guild.created_at.strftime("%d.%m.%Y"))

        await ctx.send(embed=embed)

    # ================= BOT INFO =================
    @commands.command()
    async def botinfo(self, ctx):
        embed = discord.Embed(
            title="🤖 Bot Info",
            description=f"Servers: {len(self.bot.guilds)}",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Utility(bot))
