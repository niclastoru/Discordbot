import discord
from discord.ext import commands
import json
import os

FILE = "/data/embeds.json"

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

embed_data = load_data()


# ================= BUILD =================
def build_embed(data):
    return discord.Embed(
        title=data.get("title") or "No Title",
        description=data.get("description") or "No Description",
        color=data.get("color", 0x5865F2)
    )


# ================= VIEW =================
class EmbedEditor(discord.ui.View):
    def __init__(self, bot, guild_id, name):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.name = name

    def get_data(self):
        return embed_data[self.guild_id][self.name]

    async def update_embed(self, interaction):
        embed = build_embed(self.get_data())
        await interaction.response.edit_message(embed=embed, view=self)

    # ===== TITLE =====
    @discord.ui.button(label="Title", style=discord.ButtonStyle.primary)
    async def title(self, interaction, button):
        await interaction.response.send_message("Send new title", ephemeral=True)

        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
        )

        self.get_data()["title"] = msg.content
        save_data(embed_data)

        await interaction.followup.send("✅ Updated", ephemeral=True)

    # ===== DESCRIPTION =====
    @discord.ui.button(label="Description", style=discord.ButtonStyle.primary)
    async def desc(self, interaction, button):
        await interaction.response.send_message("Send new description", ephemeral=True)

        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
        )

        self.get_data()["description"] = msg.content
        save_data(embed_data)

        await interaction.followup.send("✅ Updated", ephemeral=True)

    # ===== COLOR =====
    @discord.ui.button(label="Color", style=discord.ButtonStyle.secondary)
    async def color(self, interaction, button):
        await interaction.response.send_message("Send hex color (#ff0000)", ephemeral=True)

        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
        )

        try:
            self.get_data()["color"] = int(msg.content.replace("#", ""), 16)
            save_data(embed_data)
            await interaction.followup.send("✅ Updated", ephemeral=True)
        except:
            await interaction.followup.send("❌ Invalid color", ephemeral=True)

    # ===== SEND =====
    @discord.ui.button(label="Send", style=discord.ButtonStyle.green)
    async def send_embed(self, interaction, button):
        await interaction.channel.send(embed=build_embed(self.get_data()))
        await interaction.response.send_message("✅ Sent", ephemeral=True)


# ================= COG =================
class EmbedBuilder(commands.Cog, name="🧩 Embeds"):
    def __init__(self, bot):
        self.bot = bot

    # ===== CREATE =====
    @commands.command()
    async def embed_create(self, ctx, name: str):
        gid = str(ctx.guild.id)

        embed_data.setdefault(gid, {})

        if name in embed_data[gid]:
            return await ctx.send("❌ Already exists")

        embed_data[gid][name] = {
            "title": None,
            "description": None,
            "color": 0x5865F2
        }

        save_data(embed_data)
        await ctx.send(f"✅ Created `{name}`")

    # ===== DELETE =====
    @commands.command()
    async def embed_delete(self, ctx, name: str):
        gid = str(ctx.guild.id)

        if name not in embed_data.get(gid, {}):
            return await ctx.send("❌ Not found")

        del embed_data[gid][name]
        save_data(embed_data)

        await ctx.send("🗑️ Deleted")

    # ===== SHOW =====
    @commands.command()
    async def embed_show(self, ctx, name: str):
        gid = str(ctx.guild.id)

        if name not in embed_data.get(gid, {}):
            return await ctx.send("❌ Not found")

        embed = build_embed(embed_data[gid][name])
        view = EmbedEditor(self.bot, gid, name)

        await ctx.send(embed=embed, view=view)

    # ===== LIST =====
    @commands.command()
    async def embed_list(self, ctx):
        gid = str(ctx.guild.id)

        if gid not in embed_data or not embed_data[gid]:
            return await ctx.send("❌ No embeds")

        names = "\n".join(f"• {n}" for n in embed_data[gid].keys())

        embed = discord.Embed(
            title="📋 Embed List",
            description=names,
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed)


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
