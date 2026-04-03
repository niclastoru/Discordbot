import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

FILE = "/data/antinuke.json"

# ================= LOAD =================
def load_data():
    try:
        if not os.path.exists(FILE):
            with open(FILE, "w") as f:
                json.dump({}, f)

        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# ================= SAVE =================
def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

antinuke_data = load_data()

# ================= TRACK =================
actions = {}

LIMIT = 3
TIME = 10


class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= ENABLE =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx, state: str = None):

        guild_id = str(ctx.guild.id)

        if guild_id not in antinuke_data:
            antinuke_data[guild_id] = {
                "enabled": False,
                "whitelist": []
            }

        if state == "on":
            antinuke_data[guild_id]["enabled"] = True
            save_data(antinuke_data)
            await ctx.send("🛡️ AntiNuke Enabled")

        elif state == "off":
            antinuke_data[guild_id]["enabled"] = False
            save_data(antinuke_data)
            await ctx.send("❌ AntiNuke Disabled")

        else:
            await ctx.send("Usage: `?antinuke on/off`")

    # ================= WHITELIST =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def an(self, ctx, action=None, user: discord.Member = None):

        guild_id = str(ctx.guild.id)

        if guild_id not in antinuke_data:
            antinuke_data[guild_id] = {
                "enabled": False,
                "whitelist": []
            }

        # ===== ADD =====
        if action == "add" and user:

            if user.id in antinuke_data[guild_id]["whitelist"]:
                return await ctx.send("❌ Already whitelisted")

            antinuke_data[guild_id]["whitelist"].append(user.id)
            save_data(antinuke_data)

            return await ctx.send(f"✅ {user.mention} added to whitelist")

        # ===== REMOVE =====
        elif action == "remove" and user:

            if user.id not in antinuke_data[guild_id]["whitelist"]:
                return await ctx.send("❌ Not in whitelist")

            antinuke_data[guild_id]["whitelist"].remove(user.id)
            save_data(antinuke_data)

            return await ctx.send(f"🗑️ {user.mention} removed")

        # ===== LIST =====
        elif action == "list":

            users = [
                ctx.guild.get_member(uid)
                for uid in antinuke_data[guild_id]["whitelist"]
            ]

            text = "\n".join([u.mention for u in users if u]) or "No whitelist"

            return await ctx.send(embed=discord.Embed(
                title="🛡️ AntiNuke Whitelist",
                description=text,
                color=discord.Color.blurple()
            ))

        else:
            await ctx.send(
                "Usage:\n"
                "`?an add @user`\n"
                "`?an remove @user`\n"
                "`?an list`"
            )

    # ================= CHECK =================
    def is_whitelisted(self, guild_id, user):
        return (
            user.id in antinuke_data.get(guild_id, {}).get("whitelist", [])
            or user.id == user.guild.owner_id
            or user.guild_permissions.administrator
        )

    async def punish(self, guild, user, reason):
        try:
            await guild.ban(user, reason=f"AntiNuke: {reason}")
        except:
            pass

    def check_limit(self, guild_id, user_id):

        now = datetime.utcnow()

        if guild_id not in actions:
            actions[guild_id] = {}

        if user_id not in actions[guild_id]:
            actions[guild_id][user_id] = []

        actions[guild_id][user_id].append(now)

        actions[guild_id][user_id] = [
            t for t in actions[guild_id][user_id]
            if now - t < timedelta(seconds=TIME)
        ]

        return len(actions[guild_id][user_id]) >= LIMIT

    # ================= CHANNEL DELETE =================
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        guild = channel.guild
        guild_id = str(guild.id)

        if not antinuke_data.get(guild_id, {}).get("enabled"):
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user

            if self.is_whitelisted(guild_id, user):
                return

            if self.check_limit(guild_id, user.id):
                await self.punish(guild, user, "Mass Channel Delete")

    # ================= ROLE DELETE =================
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        guild = role.guild
        guild_id = str(guild.id)

        if not antinuke_data.get(guild_id, {}).get("enabled"):
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            user = entry.user

            if self.is_whitelisted(guild_id, user):
                return

            if self.check_limit(guild_id, user.id):
                await self.punish(guild, user, "Mass Role Delete")

    # ================= BAN =================
    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):

        guild_id = str(guild.id)

        if not antinuke_data.get(guild_id, {}).get("enabled"):
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            user = entry.user

            if self.is_whitelisted(guild_id, user):
                return

            if self.check_limit(guild_id, user.id):
                await self.punish(guild, user, "Mass Ban")


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
