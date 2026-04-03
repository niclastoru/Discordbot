import discord
from discord.ext import commands
import json
import os

FILE = "/data/embeds.json"

def load_data():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)
    with open(FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

embed_data = load_data()


# ================= BUILD =================
def build_embed(data):
    embed = discord.Embed(
        title=data["title"],
        description=data["description"],
        color=data["color"]
    )

    if data["image"]:
        embed.set_image(url=data["image"])

    if data["thumbnail"]:
        embed.set_thumbnail(url=data["thumbnail"])

    if data["footer"]:
        embed.set_footer(text=data["footer"])

    if data["author"]:
        embed.set_author(name=data["author"])

    for f in data["fields"]:
        embed.add_field(name=f["name"], value=f["value"], inline=False)

    return embed


# ================= DROPDOWN =================
class EditorDropdown(discord.ui.Select):
    def __init__(self, editor):
        self.editor = editor

        options = [
            discord.SelectOption(label="Edit Title"),
            discord.SelectOption(label="Edit Description"),
            discord.SelectOption(label="Edit Color"),
            discord.SelectOption(label="Edit Image"),
            discord.SelectOption(label="Edit Thumbnail"),
            discord.SelectOption(label="Edit Footer"),
            discord.SelectOption(label="Add Field"),
            discord.SelectOption(label="Clear Fields"),
        ]

        super().__init__(
            placeholder="Select what to edit",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        choice = self.values[0]
        data = self.editor.get_data()

        if choice == "Edit Title":
            await interaction.followup.send("Send title")
            msg = await self.editor.bot.wait_for("message", check=check)
            data["title"] = msg.content

        elif choice == "Edit Description":
            await interaction.followup.send("Send description")
            msg = await self.editor.bot.wait_for("message", check=check)
            data["description"] = msg.content

        elif choice == "Edit Color":
            await interaction.followup.send("Send hex (#ff0000)")
            msg = await self.editor.bot.wait_for("message", check=check)
            try:
                data["color"] = int(msg.content.replace("#", ""), 16)
            except:
                return await interaction.followup.send("Invalid color")

        elif choice == "Edit Image":
            await interaction.followup.send("Send image URL")
            msg = await self.editor.bot.wait_for("message", check=check)
            data["image"] = msg.content

        elif choice == "Edit Thumbnail":
            await interaction.followup.send("Send thumbnail URL")
            msg = await self.editor.bot.wait_for("message", check=check)
            data["thumbnail"] = msg.content

        elif choice == "Edit Footer":
            await interaction.followup.send("Send footer")
            msg = await self.editor.bot.wait_for("message", check=check)
            data["footer"] = msg.content

        elif choice == "Add Field":
            await interaction.followup.send("Field title?")
            title = await self.editor.bot.wait_for("message", check=check)

            await interaction.followup.send("Field value?")
            value = await self.editor.bot.wait_for("message", check=check)

            data["fields"].append({
                "name": title.content,
                "value": value.content
            })

        elif choice == "Clear Fields":
            data["fields"] = []

        save_data(embed_data)
        await self.editor.refresh(interaction)


# ================= VIEW =================
class EmbedEditor(discord.ui.View):
    def __init__(self, bot, guild_id, name):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.name = name

        self.add_item(EditorDropdown(self))

    def get_data(self):
        return embed_data[self.guild_id][self.name]

    async def refresh(self, interaction):
        embed = build_embed(self.get_data())
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Send", style=discord.ButtonStyle.green)
    async def send(self, interaction, button):
        await interaction.channel.send(embed=build_embed(self.get_data()))
        await interaction.response.send_message("✅ Sent", ephemeral=True)


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
            "author": None,
            "fields": []
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

        embed = build_embed(embed_data[gid][name])
        view = EmbedEditor(self.bot, gid, name)

        await ctx.send(embed=embed, view=view)


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
