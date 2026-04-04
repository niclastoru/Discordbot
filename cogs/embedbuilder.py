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
    embed = discord.Embed(
        title=data.get("title") or "No Title",
        description=data.get("description") or "No Description",
        color=data.get("color", 0x5865F2)
    )

    if data.get("image"):
        embed.set_image(url=data["image"])

    if data.get("thumbnail"):
        embed.set_thumbnail(url=data["thumbnail"])

    if data.get("footer"):
        embed.set_footer(text=data["footer"])

    if data.get("author"):
        embed.set_author(name=data["author"])

    return embed


# ================= VIEW =================
class EmbedEditor(discord.ui.View):
    def __init__(self, bot, gid, name):
        super().__init__(timeout=None)
        self.bot = bot
        self.gid = gid
        self.name = name

    def data(self):
        return embed_data[self.gid][self.name]

    async def refresh(self, interaction):
        await interaction.response.edit_message(
            embed=build_embed(self.data()),
            view=self
        )

    # ========= BASIC =========
    @discord.ui.button(label="Edit Basic", style=discord.ButtonStyle.primary)
    async def basic(self, interaction, button):
        await interaction.response.send_message("Send: title | description", ephemeral=True)

        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
        )

        try:
            title, desc = msg.content.split("|", 1)
            self.data()["title"] = title.strip()
            self.data()["description"] = desc.strip()
            save_data(embed_data)
            await self.refresh(interaction)
        except:
            await interaction.followup.send("❌ Format: title | description", ephemeral=True)

    # ========= AUTHOR =========
    @discord.ui.button(label="Edit Author", style=discord.ButtonStyle.secondary)
    async def author(self, interaction, button):
        await interaction.response.send_message("Send author name", ephemeral=True)

        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
        )

        self.data()["author"] = msg.content
        save_data(embed_data)
        await self.refresh(interaction)

    # ========= FOOTER =========
    @discord.ui.button(label="Edit Footer", style=discord.ButtonStyle.secondary)
    async def footer(self, interaction, button):
        await interaction.response.send_message("Send footer", ephemeral=True)

        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
        )

        self.data()["footer"] = msg.content
        save_data(embed_data)
        await self.refresh(interaction)

    # ========= MEDIA =========
    @discord.ui.button(label="Edit Images", style=discord.ButtonStyle.secondary)
    async def images(self, interaction, button):
        await interaction.response.send_message("Send: image_url | thumbnail_url", ephemeral=True)

        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
        )

        try:
            img, thumb = msg.content.split("|", 1)
            self.data()["image"] = img.strip()
            self.data()["thumbnail"] = thumb.strip()
            save_data(embed_data)
            await self.refresh(interaction)
        except:
            await interaction.followup.send("❌ Format: image | thumbnail", ephemeral=True)

    # ========= COLOR =========
    @discord.ui.button(label="Color", style=discord.ButtonStyle.secondary)
    async def color(self, interaction, button):
        await interaction.response.send_message("Send hex (#ff0000)", ephemeral=True)

        msg = await self.bot.wait_for(
            "message",
            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
        )

        try:
            self.data()["color"] = int(msg.content.replace("#", ""), 16)
            save_data(embed_data)
            await self.refresh(interaction)
        except:
            await interaction.followup.send("❌ Invalid color", ephemeral=True)

    # ========= SEND =========
    @discord.ui.button(label="Send", style=discord.ButtonStyle.green)
    async def send_embed(self, interaction, button):
        await interaction.channel.send(embed=build_embed(self.data()))
        await interaction.response.defer()


# ================= COG =================
class EmbedBuilder(commands.Cog, name="🧩 Embeds"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def embed_create(self, ctx, name: str):
        gid = str(ctx.guild.id)

        embed_data.setdefault(gid, {})

        embed_data[gid][name] = {
            "title": None,
            "description": None,
            "color": 0x5865F2,
            "image": None,
            "thumbnail": None,
            "footer": None,
            "author": None
        }

        save_data(embed_data)
        await ctx.send(f"✅ Created `{name}`")

    @commands.command()
    async def embed_delete(self, ctx, name: str):
        gid = str(ctx.guild.id)

        if name not in embed_data.get(gid, {}):
            return await ctx.send("❌ Not found")

        del embed_data[gid][name]
        save_data(embed_data)

        await ctx.send("🗑️ Deleted")

    @commands.command()
    async def embed_show(self, ctx, name: str):
        gid = str(ctx.guild.id)

        if name not in embed_data.get(gid, {}):
            return await ctx.send("❌ Not found")

        view = EmbedEditor(self.bot, gid, name)

        await ctx.send(
            embed=build_embed(embed_data[gid][name]),
            view=view
        )

    @commands.command()
    async def embed_list(self, ctx):
        gid = str(ctx.guild.id)

        if gid not in embed_data or not embed_data[gid]:
            return await ctx.send("❌ No embeds")

        text = "\n".join(f"• {x}" for x in embed_data[gid])

        await ctx.send(embed=discord.Embed(
            title="📋 Embeds",
            description=text,
            color=discord.Color.blurple()
        ))


async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
