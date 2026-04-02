import discord
from discord.ext import commands
import json
import os

FILE = "staff.json"

# ================= LOAD / SAVE =================

def load_data():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)

    with open(FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

staff_data = load_data()

# ================= COG =================

class Staff(commands.Cog, name="👑 Staff"):
    def __init__(self, bot):
        self.bot = bot

    # ================= SETTINGS STAFF =================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def staff(self, ctx, action=None, role: discord.Role = None):

        guild_id = str(ctx.guild.id)

        # Server vorbereiten
        if guild_id not in staff_data:
            staff_data[guild_id] = []

        # ================= ADD =================
        if action == "add" and role:

            if role.id in staff_data[guild_id]:
                return await ctx.send("❌ Role already added")

            staff_data[guild_id].append(role.id)
            save_data(staff_data)

            return await ctx.send(embed=discord.Embed(
                title="✅ Staff Role Added",
                description=f"{role.mention} added",
                color=discord.Color.green()
            ))

        # ================= REMOVE =================
        elif action == "remove" and role:

            if role.id not in staff_data[guild_id]:
                return await ctx.send("❌ Role not found")

            staff_data[guild_id].remove(role.id)
            save_data(staff_data)

            return await ctx.send(embed=discord.Embed(
                title="🗑️ Staff Role Removed",
                description=f"{role.mention} removed",
                color=discord.Color.orange()
            ))

        # ================= LIST =================
        elif action == "list":

            roles = [ctx.guild.get_role(r) for r in staff_data[guild_id]]

            text = "\n".join([r.mention for r in roles if r]) or "No roles set"

            return await ctx.send(embed=discord.Embed(
                title="📋 Staff Roles",
                description=text,
                color=discord.Color.blurple()
            ))

        else:
            return await ctx.send(
                "Usage:\n"
                "`?staff add @role`\n"
                "`?staff remove @role`\n"
                "`?staff list`"
            )

# ================= CHECK FUNCTION =================

def is_staff(member):
    guild_id = str(member.guild.id)

    if guild_id not in staff_data:
        return False

    return any(role.id in staff_data[guild_id] for role in member.roles)

# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(Staff(bot))
