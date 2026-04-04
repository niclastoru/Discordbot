import discord
from discord.ext import commands
import json
import os

FILE = "/data/tickets.json"

def load():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)
    with open(FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()


# ================= CHECK STAFF =================
def is_staff(member, guild_id):
    return guild_id in data and any(role.id in data[guild_id].get("staff_roles", []) for role in member.roles)


# ================= PANEL =================
class Panel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Support", style=discord.ButtonStyle.primary)
    async def support(self, interaction, _):
        await create_ticket(interaction, "support")

    @discord.ui.button(label="👑 Admin", style=discord.ButtonStyle.danger)
    async def admin(self, interaction, _):
        await create_ticket(interaction, "admin")


# ================= TICKET VIEW =================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary)
    async def claim(self, interaction, _):

        gid = str(interaction.guild.id)

        if not is_staff(interaction.user, gid):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)

        if interaction.channel.topic and "claimed" in interaction.channel.topic:
            return await interaction.response.send_message("❌ Already claimed", ephemeral=True)

        await interaction.channel.edit(topic=f"claimed:{interaction.user.id}")

        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

    @discord.ui.button(label="Add", style=discord.ButtonStyle.secondary)
    async def add(self, interaction, _):

        if not is_staff(interaction.user, str(interaction.guild.id)):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)

        await interaction.response.send_message("Send user ID", ephemeral=True)

        msg = await interaction.client.wait_for("message", check=lambda m: m.author == interaction.user)

        user = await interaction.guild.fetch_member(int(msg.content))

        await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)

        await interaction.followup.send(f"✅ Added {user.mention}")

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.secondary)
    async def rename(self, interaction, _):

        await interaction.response.send_message("Send new name", ephemeral=True)

        msg = await interaction.client.wait_for("message", check=lambda m: m.author == interaction.user)

        await interaction.channel.edit(name=msg.content)

        await interaction.followup.send("✅ Renamed")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction, _):

        gid = str(interaction.guild.id)
        log_channel = interaction.guild.get_channel(data[gid].get("logs"))

        messages = []
        async for m in interaction.channel.history(limit=200):
            messages.append(f"{m.author}: {m.content}")

        transcript = "\n".join(messages[::-1])

        file = discord.File(fp=bytes(transcript, "utf-8"), filename="transcript.txt")

        if log_channel:
            await log_channel.send(f"📁 Ticket closed by {interaction.user.mention}", file=file)

        await interaction.channel.delete()


# ================= CREATE =================
async def create_ticket(interaction, ttype):

    guild = interaction.guild
    user = interaction.user
    gid = str(guild.id)

    if gid not in data:
        return await interaction.response.send_message("❌ Setup missing", ephemeral=True)

    # Limit 1 Ticket
    for ch in guild.text_channels:
        if ch.name.endswith(str(user.id)):
            return await interaction.response.send_message("❌ You already have a ticket", ephemeral=True)

    category = guild.get_channel(data[gid]["category"])

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    # Staff Zugriff
    for role_id in data[gid].get("staff_roles", []):
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel = await guild.create_text_channel(
        name=f"{ttype}-{user.id}",
        category=category,
        overwrites=overwrites
    )

    await channel.send(
        content=f"{user.mention}",
        embed=discord.Embed(
            title=f"{ttype.capitalize()} Ticket",
            description="Support will assist you shortly.",
            color=discord.Color.blurple()
        ),
        view=TicketView()
    )

    await interaction.response.send_message(f"✅ Created {channel.mention}", ephemeral=True)


# ================= COG =================
class Tickets(commands.Cog, name="🎫 Tickets"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx):
        embed = discord.Embed(
            title="🎫 Ticket System",
            description="Choose a ticket",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=Panel())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setticket(self, ctx, category: discord.CategoryChannel):
        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid]["category"] = category.id
        save(data)
        await ctx.send("✅ Category set")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketlogs(self, ctx, channel: discord.TextChannel):
        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid]["logs"] = channel.id
        save(data)
        await ctx.send("✅ Logs channel set")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketstaff(self, ctx, role: discord.Role):
        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid].setdefault("staff_roles", [])

        if role.id in data[gid]["staff_roles"]:
            data[gid]["staff_roles"].remove(role.id)
            await ctx.send("❌ Removed")
        else:
            data[gid]["staff_roles"].append(role.id)
            await ctx.send("✅ Added")

        save(data)


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Tickets(bot))
