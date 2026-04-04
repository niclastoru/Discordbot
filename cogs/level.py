import discord
from discord.ext import commands
import json
import os
import time

FILE = "/data/levels.json"

# ================= LOAD =================
def load_data():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)
    with open(FILE, "r") as f:
        return json.load(f)

# ================= SAVE =================
def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

level_data = load_data()

cooldowns = {}

# ================= XP SYSTEM =================
def get_level(xp):
    level = 0
    while xp >= (level + 1) ** 2 * 100:
        level += 1
    return level

# ================= COG =================
class Level(commands.Cog, name="📊 Level"):
    def __init__(self, bot):
        self.bot = bot

    # ================= MESSAGE XP =================
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        # Server setup
        if guild_id not in level_data:
            level_data[guild_id] = {
                "users": {},
                "no_xp_channels": [],
                "level_channel": None
            }

        # NoXP Channel check
        if message.channel.id in level_data[guild_id]["no_xp_channels"]:
            return

        # Cooldown (5 Sekunden)
        now = time.time()
        if user_id in cooldowns and now - cooldowns[user_id] < 5:
            return

        cooldowns[user_id] = now

        # User erstellen
        if user_id not in level_data[guild_id]["users"]:
            level_data[guild_id]["users"][user_id] = {
                "xp": 0,
                "level": 0
            }

        user = level_data[guild_id]["users"][user_id]

        # XP geben
        user["xp"] += 10

        old_level = user["level"]
        new_level = get_level(user["xp"])

        if new_level > old_level:
            user["level"] = new_level

            channel_id = level_data[guild_id]["level_channel"]
            channel = message.guild.get_channel(channel_id) if channel_id else message.channel

            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} reached level **{new_level}**",
                color=discord.Color.green()
            )

            await channel.send(embed=embed)

        save_data(level_data)

    # ================= RANK =================
    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in level_data or user_id not in level_data[guild_id]["users"]:
            return await ctx.send("❌ No data")

        user = level_data[guild_id]["users"][user_id]

        embed = discord.Embed(
            title=f"{member.name}'s Rank",
            color=discord.Color.blurple()
        )

        embed.add_field(name="Level", value=user["level"])
        embed.add_field(name="XP", value=user["xp"])

        await ctx.send(embed=embed)

    # ================= LEADERBOARD =================
    @commands.command()
    async def leaderboard(self, ctx):
        guild_id = str(ctx.guild.id)

        if guild_id not in level_data:
            return await ctx.send("❌ No data")

        users = level_data[guild_id]["users"]

        sorted_users = sorted(users.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]

        text = ""
        for i, (uid, data) in enumerate(sorted_users, start=1):
            user = await self.bot.fetch_user(int(uid))
            text += f"**{i}.** {user.name} - {data['xp']} XP\n"

        embed = discord.Embed(
            title="🏆 Leaderboard",
            description=text,
            color=discord.Color.gold()
        )

        await ctx.send(embed=embed)

    # ================= SET LEVEL CHANNEL =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlevel(self, ctx):
        guild_id = str(ctx.guild.id)

        if guild_id not in level_data:
            level_data[guild_id] = {
                "users": {},
                "no_xp_channels": [],
                "level_channel": None
            }

        level_data[guild_id]["level_channel"] = ctx.channel.id
        save_data(level_data)

        await ctx.send("✅ Level channel set")

    # ================= NO XP =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def noxp(self, ctx):
        guild_id = str(ctx.guild.id)

        if guild_id not in level_data:
            return

        if ctx.channel.id in level_data[guild_id]["no_xp_channels"]:
            level_data[guild_id]["no_xp_channels"].remove(ctx.channel.id)
            await ctx.send("❌ XP enabled here")
        else:
            level_data[guild_id]["no_xp_channels"].append(ctx.channel.id)
            await ctx.send("✅ No XP channel")

        save_data(level_data)


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Level(bot))
