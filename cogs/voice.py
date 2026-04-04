import discord
from discord.ext import commands
import json
import os

FILE = "/data/voice.json"

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
def is_owner(user, channel):
    return data.get(str(channel.id), {}).get("owner") == user.id


# ================= MODALS =================

class RenameModal(discord.ui.Modal, title="Rename Channel"):
    name = discord.ui.TextInput(label="New Name")

    def __init__(self, vc):
        super().__init__()
        self.vc = vc

    async def on_submit(self, interaction):
        await self.vc.edit(name=self.name.value)
        await interaction.response.send_message("✅ Renamed", ephemeral=True)


class BitrateModal(discord.ui.Modal, title="Set Bitrate"):
    bitrate = discord.ui.TextInput(label="Bitrate (8000 - 96000)")

    def __init__(self, vc):
        super().__init__()
        self.vc = vc

    async def on_submit(self, interaction):
        try:
            b = int(self.bitrate.value)
            await self.vc.edit(bitrate=b)
            await interaction.response.send_message("✅ Bitrate updated", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Invalid", ephemeral=True)


class KickModal(discord.ui.Modal, title="Kick User"):
    user_id = discord.ui.TextInput(label="User ID")

    def __init__(self, vc):
        super().__init__()
        self.vc = vc

    async def on_submit(self, interaction):
        member = await interaction.guild.fetch_member(int(self.user_id.value))
        await member.move_to(None)
        await interaction.response.send_message("👢 User kicked", ephemeral=True)


# ================= VIEW =================

class VoicePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_vc(self, interaction):
        return interaction.user.voice.channel if interaction.user.voice else None

    def check(self, interaction):
        vc = self.get_vc(interaction)
        return vc and is_owner(interaction.user, vc)

    @discord.ui.button(label="🔒", style=discord.ButtonStyle.secondary)
    async def lock(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        vc = self.get_vc(interaction)
        await vc.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Locked", ephemeral=True)

    @discord.ui.button(label="🔓", style=discord.ButtonStyle.secondary)
    async def unlock(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        vc = self.get_vc(interaction)
        await vc.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Unlocked", ephemeral=True)

    @discord.ui.button(label="👻", style=discord.ButtonStyle.secondary)
    async def hide(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        vc = self.get_vc(interaction)
        await vc.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message("👻 Hidden", ephemeral=True)

    @discord.ui.button(label="👁", style=discord.ButtonStyle.secondary)
    async def reveal(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        vc = self.get_vc(interaction)
        await vc.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message("👁 Visible", ephemeral=True)

    @discord.ui.button(label="🎤 Claim", style=discord.ButtonStyle.primary)
    async def claim(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc:
            return

        data[str(vc.id)]["owner"] = interaction.user.id
        save(data)

        await interaction.response.send_message("👑 You are now owner", ephemeral=True)

    @discord.ui.button(label="➕", style=discord.ButtonStyle.secondary)
    async def increase(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        vc = self.get_vc(interaction)
        await vc.edit(user_limit=vc.user_limit + 1)
        await interaction.response.send_message("➕ Limit increased", ephemeral=True)

    @discord.ui.button(label="➖", style=discord.ButtonStyle.secondary)
    async def decrease(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        vc = self.get_vc(interaction)
        await vc.edit(user_limit=max(0, vc.user_limit - 1))
        await interaction.response.send_message("➖ Limit decreased", ephemeral=True)

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.secondary)
    async def rename(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        await interaction.response.send_modal(RenameModal(vc))

    @discord.ui.button(label="📶 Bitrate", style=discord.ButtonStyle.secondary)
    async def bitrate(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        await interaction.response.send_modal(BitrateModal(vc))

    @discord.ui.button(label="👢 Kick", style=discord.ButtonStyle.danger)
    async def kick(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        await interaction.response.send_modal(KickModal(vc))

    @discord.ui.button(label="ℹ️ Info", style=discord.ButtonStyle.secondary)
    async def info(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc:
            return

        embed = discord.Embed(
            title="Voice Info",
            description=f"Name: {vc.name}\nUsers: {len(vc.members)}\nLimit: {vc.user_limit}",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= COG =================

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        gid = str(member.guild.id)

        if gid not in data:
            return

        join = data[gid].get("join")

        # JOIN CREATE
        if after.channel and after.channel.id == join:
            vc = await member.guild.create_voice_channel(
                name=member.name,
                category=after.channel.category
            )

            await member.move_to(vc)

            data[str(vc.id)] = {"owner": member.id}
            save(data)

        # AUTO DELETE + CLAIM
        if before.channel:
            cid = str(before.channel.id)

            if cid in data:
                if len(before.channel.members) == 0:
                    del data[cid]
                    save(data)
                    await before.channel.delete()
                else:
                    if data[cid]["owner"] == member.id:
                        new_owner = before.channel.members[0]
                        data[cid]["owner"] = new_owner.id
                        save(data)

    @commands.command()
    async def setvoice(self, ctx, channel: discord.VoiceChannel):
        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid]["join"] = channel.id
        save(data)
        await ctx.send("✅ Join channel set")

    @commands.command()
    async def voicepanel(self, ctx):

        embed = discord.Embed(
            title="🎛 VoiceMaster",
            description="Control your channel with buttons",
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed, view=VoicePanel())


async def setup(bot):
    await bot.add_cog(Voice(bot))
