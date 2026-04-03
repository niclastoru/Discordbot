import discord
from discord.ext import commands
import json
import os

FILE = "/data/welcome.json"

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

welcome_data = load_data()


class Welcome(commands.Cog, name="🎉 Welcome"):
    def __init__(self, bot):
        self.bot = bot

    # ================= SETUP COMMAND =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx, action: str = None, *, text: str = None):

        guild_id = str(ctx.guild.id)

        if guild_id not in welcome_data:
            welcome_data[guild_id] = {
                "channel": None,
                "join": None,
                "leave": None,
                "boost": None
            }

        # ===== CHANNEL =====
        if action == "channel":
            welcome_data[guild_id]["channel"] = ctx.channel.id
            save_data(welcome_data)

            return await ctx.send("✅ Welcome channel set")

        # ===== JOIN =====
        elif action == "join" and text:
            welcome_data[guild_id]["join"] = text
            save_data(welcome_data)

            return await ctx.send("✅ Join message saved")

        # ===== LEAVE =====
        elif action == "leave" and text:
            welcome_data[guild_id]["leave"] = text
            save_data(welcome_data)

            return await ctx.send("✅ Leave message saved")

        # ===== BOOST =====
        elif action == "boost" and text:
            welcome_data[guild_id]["boost"] = text
            save_data(welcome_data)

            return await ctx.send("✅ Boost message saved")

        # ===== HELP =====
        else:
            return await ctx.send(
                "**Setup Commands:**\n"
                "`?welcome channel`\n"
                "`?welcome join <text>`\n"
                "`?welcome leave <text>`\n"
                "`?welcome boost <text>`\n\n"
                "**Placeholders:**\n"
                "`{user}` `{server}`"
            )

    # ================= JOIN EVENT =================
    @commands.Cog.listener()
    async def on_member_join(self, member):

        guild_id = str(member.guild.id)
        data = welcome_data.get(guild_id)

        if not data:
            return

        if not data.get("channel") or not data.get("join"):
            return

        channel = member.guild.get_channel(data["channel"])
        if not channel:
            return

        msg = data["join"] \
            .replace("{user}", member.mention) \
            .replace("{server}", member.guild.name)

        await channel.send(msg)

    # ================= LEAVE EVENT =================
    @commands.Cog.listener()
    async def on_member_remove(self, member):

        guild_id = str(member.guild.id)
        data = welcome_data.get(guild_id)

        if not data:
            return

        if not data.get("channel") or not data.get("leave"):
            return

        channel = member.guild.get_channel(data["channel"])
        if not channel:
            return

        msg = data["leave"] \
            .replace("{user}", member.name) \
            .replace("{server}", member.guild.name)

        await channel.send(msg)

    # ================= BOOST EVENT =================
    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        if before.premium_since is None and after.premium_since is not None:

            guild_id = str(after.guild.id)
            data = welcome_data.get(guild_id)

            if not data:
                return

            if not data.get("channel") or not data.get("boost"):
                return

            channel = after.guild.get_channel(data["channel"])
            if not channel:
                return

            msg = data["boost"] \
                .replace("{user}", after.mention) \
                .replace("{server}", after.guild.name)

            await channel.send(msg)


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Welcome(bot))
