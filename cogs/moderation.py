import discord
from discord.ext import commands
from datetime import timedelta

def parse_time(time_str):
    try:
        unit = time_str[-1]
        value = int(time_str[:-1])

        if unit == "s":
            return timedelta(seconds=value)
        elif unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
    except:
        return None


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= BAN =================
@commands.command()
@commands.has_permissions(ban_members=True)
async def ban(self, ctx, user: str, *, reason="No reason provided"):

    try:
        if user.isdigit():
            user = await self.bot.fetch_user(int(user))
        else:
            user = ctx.message.mentions[0]

        # DM vorher
        try:
            embed = discord.Embed(
                title="🔨 You were banned",
                description=f"Server: {ctx.guild.name}\nReason: {reason}",
                color=discord.Color.red()
            )
            await user.send(embed=embed)
        except:
            pass  # DM blocked

        await ctx.guild.ban(user, reason=reason)

        await ctx.send(embed=discord.Embed(
            title="🔨 User Banned",
            description=f"{user} was banned\nReason: {reason}",
            color=discord.Color.red()
        ))

    except:
        await ctx.send("❌ Invalid user")


  
    # ================= UNBAN =================

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)

            embed = discord.Embed(
                title="♻️ User Unbanned",
                description=f"{user} is unbanned",
                color=discord.Color.green()
            )

            await ctx.send(embed=embed)

        except:
            await ctx.send("❌ Invalid ID")

    # ================= TIMEOUT =================
@commands.command()
@commands.has_permissions(moderate_members=True)
async def timeout(self, ctx, user: str, duration: str):

    delta = parse_time(duration)

    if not delta:
        return await ctx.send("❌ Invalid time format (10m, 1h, 1d)")

    try:
        if user.isdigit():
            member = await ctx.guild.fetch_member(int(user))
        else:
            member = ctx.message.mentions[0]

        # DM vorher
        try:
            embed = discord.Embed(
                title="🔇 You were timed out",
                description=f"Server: {ctx.guild.name}\nDuration: {duration}",
                color=discord.Color.orange()
            )
            await member.send(embed=embed)
        except:
            pass

        await member.timeout(delta)

        await ctx.send(embed=discord.Embed(
            title="🔇 User Timed Out",
            description=f"{member.mention} for {duration}",
            color=discord.Color.orange()
        ))

    except:
        await ctx.send("❌ Invalid user")

    # ================= UNTIMEOUT =================
@commands.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(self, ctx, user: str):

    try:
        if user.isdigit():
            member = await ctx.guild.fetch_member(int(user))
        else:
            member = ctx.message.mentions[0]

        await member.timeout(None)

        try:
            await member.send("🔊 Your timeout has been removed.")
        except:
            pass

        await ctx.send(embed=discord.Embed(
            title="🔊 Timeout Removed",
            description=f"{member.mention} is now free",
            color=discord.Color.green()
        ))

    except:
        await ctx.send("❌ Invalid user")
  
