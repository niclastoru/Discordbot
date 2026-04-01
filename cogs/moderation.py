import discord
from discord.ext import commands
from datetime import timedelta
import json

JAIL_FILE = "jail.json"

def load_jail():
    try:
        with open(JAIL_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_jail(data):
    with open(JAIL_FILE, "w") as f:
        json.dump(data, f, indent=4)

jail_data = load_jail()

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
                member = ctx.message.mentions[0]
                user = member

            try:
                embed = discord.Embed(
                    title="🔨 You were banned",
                    description=f"Server: {ctx.guild.name}\nReason: {reason}",
                    color=discord.Color.red()
                )
                await user.send(embed=embed)
            except:
                pass

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

            await ctx.send(embed=discord.Embed(
                title="♻️ User Unbanned",
                description=f"{user} is unbanned",
                color=discord.Color.green()
            ))

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

    # ================= SET JAIL ROLE =================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setjail(self, ctx, role: discord.Role):

        guild_id = str(ctx.guild.id)

        if guild_id not in jail_data:
            jail_data[guild_id] = {}

        jail_data[guild_id]["jail_role"] = role.id
        save_jail(jail_data)

        await ctx.send(embed=discord.Embed(
            title="🔒 Jail Role Set",
            description=f"{role.mention} is now the jail role.",
            color=discord.Color.green()
        ))

    # ================= JAIL =================

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def jail(self, ctx, member: discord.Member):

        guild_id = str(ctx.guild.id)

        if guild_id not in jail_data or "jail_role" not in jail_data[guild_id]:
            return await ctx.send("❌ Jail role not set. Use ?setjail @role")

        jail_role = ctx.guild.get_role(jail_data[guild_id]["jail_role"])

        if not jail_role:
            return await ctx.send("❌ Jail role not found")

        # Rollen speichern
        roles = [role.id for role in member.roles if role != ctx.guild.default_role]

        if "jailed_users" not in jail_data[guild_id]:
            jail_data[guild_id]["jailed_users"] = {}

        jail_data[guild_id]["jailed_users"][str(member.id)] = roles
        save_jail(jail_data)

        try:
            await member.edit(roles=[jail_role])
        except Exception as e:
            return await ctx.send(f"❌ Error:\n```{e}```")

        # DM
        try:
            await member.send(f"🔒 You have been jailed in {ctx.guild.name}")
        except:
            pass

        await ctx.send(embed=discord.Embed(
            title="🔒 User Jailed",
            description=f"{member.mention} is now jailed",
            color=discord.Color.red()
        ))
    
    # ================= UNJAIL =================

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unjail(self, ctx, member: discord.Member):

        guild_id = str(ctx.guild.id)

        if guild_id not in jail_data or "jailed_users" not in jail_data[guild_id]:
            return await ctx.send("❌ No jailed users")

        user_id = str(member.id)

        if user_id not in jail_data[guild_id]["jailed_users"]:
            return await ctx.send("❌ This user is not jailed")

        role_ids = jail_data[guild_id]["jailed_users"][user_id]

        roles = []
        for role_id in role_ids:
            role = ctx.guild.get_role(role_id)
            if role:
                roles.append(role)

        await member.edit(roles=roles)

        del jail_data[guild_id]["jailed_users"][user_id]
        save_jail(jail_data)

        # DM
        try:
            await member.send(f"🔓 You have been unjailed in {ctx.guild.name}")
        except:
            pass

        await ctx.send(embed=discord.Embed(
            title="🔓 User Unjailed",
            description=f"{member.mention} is free",
            color=discord.Color.green()
        ))




async def setup(bot):
    await bot.add_cog(Moderation(bot))
