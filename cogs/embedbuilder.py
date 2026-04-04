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


# ================= MODALS =================

class BasicModal(discord.ui.Modal, title="Edit Basic Information"):

    title_input = discord.ui.TextInput(label="Title", required=False)
    desc_input = discord.ui.TextInput(label="Description", style=discord.TextStyle.long, required=False)
    color_input = discord.ui.TextInput(label="Hex Color (#ff0000)", required=False)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        data = self.view.get_data()

        if self.title_input.value:
            data["title"] = self.title_input.value

        if self.desc_input.value:
            data["description"] = self.desc_input.value

        if self.color_input.value:
            try:
                data["color"] = int(self.color_input.value.replace("#", ""), 16)
            except:
                pass

        save_data(embed_data)

        await interaction.response.edit_message(
            embed=build_embed(data),
            view=self.view
        )


class AuthorModal(discord.ui.Modal, title="Edit Author"):

    author_input = discord.ui.TextInput(label="Author Name")

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        data = self.view.get_data()
        data["author"] = self.author_input.value

        save_data(embed_data)

        await interaction.response.edit_message(
            embed=build_embed(data),
            view=self.view
        )


class FooterModal(discord.ui.Modal, title="Edit Footer"):

    footer_input = discord.ui.TextInput(label="Footer Text")

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        data = self.view.get_data()
        data["footer"] = self.footer_input.value

        save_data(embed_data)

        await interaction.response.edit_message(
            embed=build_embed(data),
            view=self.view
        )


class ImageModal(discord.ui.Modal, title="Edit Images"):

    image_input = discord.ui.TextInput(label="Image URL", required=False)
    thumb_input = discord.ui.TextInput(label="Thumbnail URL", required=False)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        data = self.view.get_data()

        if self.image_input.value:
            data["image"] = self.image_input.value

        if self.thumb_input.value:
            data["thumbnail"] = self.thumb_input.value

        save_data(embed_data)

        await interaction.response.edit_message(
            embed=build_embed(data),
            view=self.view
        )


# ================= VIEW =================

class EmbedEditor(discord.ui.View):
    def __init__(self, bot, gid, name):
        super().__init__(timeout=None)
        self.bot = bot
        self.gid = gid
        self.name = name

    def get_data(self):
        return embed_data[self.gid][self.name]

    # ===== BASIC =====
    @discord.ui.button(label="Edit Basic", style=discord.ButtonStyle.primary)
    async def basic(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(BasicModal(self))

    # ===== AUTHOR =====
    @discord.ui.button(label="Edit Author", style=discord.ButtonStyle.secondary)
    async def author(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(AuthorModal(self))

    # ===== FOOTER =====
    @discord.ui.button(label="Edit Footer", style=discord.ButtonStyle.secondary)
    async def footer(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(FooterModal(self))

    # ===== IMAGES =====
    @discord.ui.button(label="Edit Images", style=discord.ButtonStyle.secondary)
    async def images(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(ImageModal(self))

    # ===== SEND =====
    @discord.ui.button(label="Send", style=discord.ButtonStyle.green)
    async def send_embed(self, interaction: discord.Interaction, button):
        await interaction.channel.send(embed=build_embed(self.get_data()))
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


# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
