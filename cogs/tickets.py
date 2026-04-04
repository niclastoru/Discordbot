import discord
from discord.ext import commands

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.staff_role = None
        self.category = None
        self.log_channel = None
        self.tickets = {}

    # ================= PANEL =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def panel(self, ctx):

        embed = discord.Embed(
            title="Support Center",
            description="Select a category below to open a ticket.",
            color=discord.Color.dark_grey()
        )

        view = TicketPanel(self)
        await ctx.send(embed=embed, view=view)

    # ================= SETUP =================
    @commands.command()
    async def setstaff(self, ctx, role: discord.Role):
        self.staff_role = role
        await ctx.send("Staff role set.")

    @commands.command()
    async def setcategory(self, ctx, category: discord.CategoryChannel):
        self.category = category
        await ctx.send("Category set.")

    @commands.command()
    async def setlog(self, ctx, channel: discord.TextChannel):
        self.log_channel = channel
        await ctx.send("Log channel set.")

    @commands.command()
    async def useradd(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
        await ctx.send(f"{member.mention} added.")

    @commands.command()
    async def userremove(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(f"{member.mention} removed.")


# ================= PANEL VIEW =================
class TicketPanel(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.select(
        placeholder="Choose a category...",
        options=[
            discord.SelectOption(label="Support", description="Get help", emoji="🎫"),
            discord.SelectOption(label="Admin", description="Contact staff", emoji="⚙️")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select):

        user = interaction.user

        if user.id in self.cog.tickets:
            return await interaction.response.send_message("You already have a ticket.", ephemeral=True)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        if self.cog.staff_role:
            overwrites[self.cog.staff_role] = discord.PermissionOverwrite(view_channel=True)

        channel = await interaction.guild.create_text_channel(
            name=f"{select.values[0].lower()}-{user.name}",
            overwrites=overwrites,
            category=self.cog.category
        )

        self.cog.tickets[user.id] = channel.id

        embed = discord.Embed(
            description="Please describe your issue clearly.\nA staff member will assist you shortly.",
            color=discord.Color.dark_grey()
        )

        view = TicketButtons(self.cog)

        await channel.send(content=user.mention, embed=embed, view=view)
        await interaction.response.send_message(f"Ticket created: {channel}", ephemeral=True)


# ================= BUTTONS =================
class TicketButtons(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.secondary)
    async def claim(self, interaction: discord.Interaction, button):
        await interaction.response.send_message(f"{interaction.user.mention} claimed this ticket.")

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button):

        await interaction.response.send_message("Send new name in chat.", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        msg = await self.cog.bot.wait_for("message", check=check)
        await interaction.channel.edit(name=msg.content)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button):

        await interaction.response.send_message("Closing ticket...")

        if self.cog.log_channel:
            messages = [msg async for msg in interaction.channel.history(limit=50)]
            transcript = "\n".join([f"{m.author}: {m.content}" for m in messages])
            await self.cog.log_channel.send(f"```{transcript}```")

        await interaction.channel.delete()


# ================= LOAD =================
async def setup(bot):
    await bot.add_cog(Ticket(bot))
