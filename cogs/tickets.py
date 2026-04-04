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

def save(d):
    with open(FILE, "w") as f:
        json.dump(d, f, indent=4)

data = load()


# ================= CHECK =================
def is_staff(member, gid):
    return any(r.id in data.get(gid, {}).get("staff_roles", []) for r in member.roles)

def is_admin(member, gid):
    return any(r.id in data.get(gid, {}).get("admin_roles", []) for r in member.roles)


# ================= MODAL =================
class TicketModal(discord.ui.Modal, title="Create Ticket"):
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.long)

    def __init__(self, ttype):
        super().__init__()
        self.ttype = ttype

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, self.ttype, self.reason.value)


# ================= PANEL =================
class Panel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Support", style=discord.ButtonStyle.primary)
    async def support(self, interaction, _):
        await interaction.response.send_modal(TicketModal("support"))

    @discord.ui.button(label="👑 Admin", style=discord.ButtonStyle.danger)
    async def admin(self, interaction, _):
        if not is_admin(interaction.user, str(interaction.guild.id)):
            return await interaction.response.send_message("❌ Admin only", ephemeral=True)
        await interaction.response.send_modal(TicketModal("admin"))


# ================= CLOSE CONFIRM =================
class CloseConfirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, _):
        await close_ticket(interaction)


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

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.secondary)
    async def lock(self, interaction, _):

        if not interaction.channel.topic:
            return

        claimer = int(interaction.channel.topic.split(":")[1])

        if interaction.user.id != claimer:
            return await interaction.response.send_message("❌ Only claimer", ephemeral=True)

        for m in interaction.channel.members:
            if m.id != claimer:
                await interaction.channel.set_permissions(m, send_messages=False)

        await interaction.response.send_message("🔒 Locked")

    @discord.ui.button(label="Add", style=discord.ButtonStyle.secondary)
    async def add(self, interaction, _):

        await interaction.response.send_message("Send user ID", ephemeral=True)

        msg = await interaction.client.wait_for("message", check=lambda m: m.author == interaction.user)

        user = await interaction.guild.fetch_member(int(msg.content))
        await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)

        await interaction.followup.send(f"✅ Added {user.mention}")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction, _):
        await interaction.response.send_message("⚠️ Confirm close", view=CloseConfirm(), ephemeral=True)


# ================= CREATE =================
async def create_ticket(interaction, ttype, reason):

    guild = interaction.guild
    user = interaction.user
    gid = str(guild.id)

    if gid not in data:
        return await interaction.response.send_message("❌ Setup missing", ephemeral=True)

    # LIMIT
    for ch in guild.text_channels:
        if str(user.id) in ch.name:
            return await interaction.response.send_message("❌ Already have ticket", ephemeral=True)

    category = guild.get_channel(data[gid]["category"])

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    for r in data[gid].get("staff_roles", []):
        role = guild.get_role(r)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel = await guild.create_text_channel(
        name=f"{ttype}-{user.name}".lower(),
        category=category,
        overwrites=overwrites
    )

    embed = discord.Embed(
        title=f"{ttype.capitalize()} Ticket",
        description=f"👤 {user.mention}\n📝 {reason}",
        color=discord.Color.blurple()
    )

    await channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message(f"✅ {channel.mention}", ephemeral=True)


# ================= CLOSE =================
async def close_ticket(interaction):

    channel = interaction.channel
    gid = str(interaction.guild.id)

    log_channel = interaction.guild.get_channel(data[gid].get("logs"))

    messages = []
    async for m in channel.history(limit=200):
        messages.append(f"{m.author}: {m.content}")

    transcript = "\n".join(messages[::-1])

    file = discord.File(fp=bytes(transcript, "utf-8"), filename="transcript.txt")

    if log_channel:
        embed = discord.Embed(
            title="📁 Ticket Closed",
            description=f"{channel.name}",
            color=discord.Color.red()
        )
        await log_channel.send(embed=embed, file=file)

    await channel.delete()


# ================= COG =================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ticketpanel(self, ctx):
        await ctx.send(embed=discord.Embed(title="🎫 Ticket System"), view=Panel())

    @commands.command()
    async def setticket(self, ctx, category: discord.CategoryChannel):
        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid]["category"] = category.id
        save(data)
        await ctx.send("✅ Category set")

    @commands.command()
    async def ticketlogs(self, ctx, channel: discord.TextChannel):
        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid]["logs"] = channel.id
        save(data)
        await ctx.send("✅ Logs set")

    @commands.command()
    async def ticketstaff(self, ctx, role: discord.Role):
        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid].setdefault("staff_roles", []).append(role.id)
        save(data)
        await ctx.send("✅ Staff added")

    @commands.command()
    async def ticketadmin(self, ctx, role: discord.Role):
        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid].setdefault("admin_roles", []).append(role.id)
        save(data)
        await ctx.send("✅ Admin added")


async def setup(bot):
    await bot.add_cog(Tickets(bot))
