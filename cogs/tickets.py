import discord
from discord.ext import commands

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.staff_role = None
        self.log_channel = None
        self.category = None
        self.tickets = {}

    # ================= PANEL =================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def panel(self, ctx):

        embed = discord.Embed(
            title="🎫 Support",
            description="Klicke unten um ein Ticket zu öffnen",
            color=discord.Color.blue()
        )

        button = discord.ui.Button(label="Ticket öffnen", style=discord.ButtonStyle.primary)

        async def create_ticket(interaction):
            user = interaction.user

            if user.id in self.tickets:
                return await interaction.response.send_message("Du hast schon ein Ticket!", ephemeral=True)

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }

            if self.staff_role:
                overwrites[self.staff_role] = discord.PermissionOverwrite(view_channel=True)

            channel = await interaction.guild.create_text_channel(
                name=f"ticket-{user.name}",
                overwrites=overwrites,
                category=self.category
            )

            self.tickets[user.id] = channel.id

            await interaction.response.send_message(f"Ticket erstellt: {channel}", ephemeral=True)

            view = discord.ui.View()

            # CLAIM
            async def claim_btn(i):
                await i.response.send_message(f"{i.user.mention} hat das Ticket übernommen")

            # CLOSE
            async def close_btn(i):
                await i.response.send_message("Ticket wird geschlossen...")

                if self.log_channel:
                    messages = [msg async for msg in i.channel.history(limit=50)]
                    transcript = "\n".join([f"{m.author}: {m.content}" for m in messages])

                    await self.log_channel.send(f"```{transcript}```")

                await i.channel.delete()

            # RENAME
            async def rename_btn(i):
                await i.response.send_message("Schreib den neuen Namen:", ephemeral=True)

                def check(m):
                    return m.author == i.user and m.channel == i.channel

                msg = await self.bot.wait_for("message", check=check)
                await i.channel.edit(name=msg.content)

            view.add_item(discord.ui.Button(label="📌 Claim", style=discord.ButtonStyle.secondary, custom_id="claim"))
            view.add_item(discord.ui.Button(label="✏️ Rename", style=discord.ButtonStyle.primary, custom_id="rename"))
            view.add_item(discord.ui.Button(label="🔒 Close", style=discord.ButtonStyle.danger, custom_id="close"))

            view.children[0].callback = claim_btn
            view.children[1].callback = rename_btn
            view.children[2].callback = close_btn

            await channel.send(f"{user.mention} dein Ticket", view=view)

        view = discord.ui.View()
        button.callback = create_ticket
        view.add_item(button)

        await ctx.send(embed=embed, view=view)

    # ================= SET STAFF =================
    @commands.command()
    async def setstaff(self, ctx, role: discord.Role):
        self.staff_role = role
        await ctx.send("Staff Rolle gesetzt")

    # ================= SET LOG =================
    @commands.command()
    async def setlog(self, ctx, channel: discord.TextChannel):
        self.log_channel = channel
        await ctx.send("Log Channel gesetzt")

    # ================= SET CATEGORY =================
    @commands.command()
    async def setcategory(self, ctx, category: discord.CategoryChannel):
        self.category = category
        await ctx.send("Kategorie gesetzt")

    # ================= USER ADD =================
    @commands.command()
    async def useradd(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
        await ctx.send(f"{member.mention} hinzugefügt")

    # ================= USER REMOVE =================
    @commands.command()
    async def userremove(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(f"{member.mention} entfernt")


async def setup(bot):
    await bot.add_cog(Ticket(bot))
