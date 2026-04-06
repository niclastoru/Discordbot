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
def is_owner(user, vc):
    return data.get(str(vc.id), {}).get("owner") == user.id


# ================= MODALS =================

class RenameModal(discord.ui.Modal, title="Rename Channel"):
    name = discord.ui.TextInput(label="New Channel Name")

    def __init__(self, vc):
        super().__init__()
        self.vc = vc

    async def on_submit(self, interaction):
        await self.vc.edit(name=self.name.value)
        await interaction.response.send_message("✅ Renamed", ephemeral=True)


class LimitModal(discord.ui.Modal, title="Set User Limit"):
    limit = discord.ui.TextInput(label="User Limit (0 = unlimited)")

    def __init__(self, vc):
        super().__init__()
        self.vc = vc

    async def on_submit(self, interaction):
        try:
            limit = int(self.limit.value)
            await self.vc.edit(user_limit=limit)
            await interaction.response.send_message("✅ Limit updated", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Invalid number", ephemeral=True)


# ================= USER SELECT =================

class KickSelect(discord.ui.UserSelect):
    def __init__(self, vc):
        super().__init__(placeholder="Select user to kick", min_values=1, max_values=1)
        self.vc = vc

    async def callback(self, interaction):
        member = self.values[0]
        await member.move_to(None)
        await interaction.response.send_message(f"👢 {member} kicked", ephemeral=True)


class KickView(discord.ui.View):
    def __init__(self, vc):
        super().__init__(timeout=30)
        self.add_item(KickSelect(vc))


# ================= PANEL =================

class VoicePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_vc(self, interaction):
        return interaction.user.voice.channel if interaction.user.voice else None

    def check(self, interaction):
        vc = self.get_vc(interaction)
        return vc and is_owner(interaction.user, vc)

    # ===== ROW 1 =====
    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.secondary, row=0, custom_id="lock")
    async def lock(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)
        vc = self.get_vc(interaction)
        await vc.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Locked", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.secondary, row=0, custom_id="unlock")
    async def unlock(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)
        vc = self.get_vc(interaction)
        await vc.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Unlocked", ephemeral=True)

    @discord.ui.button(label="👻 Hide", style=discord.ButtonStyle.secondary, row=0, custom_id="hide")
    async def hide(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)
        vc = self.get_vc(interaction)
        await vc.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message("👻 Hidden", ephemeral=True)

    @discord.ui.button(label="👁 Show", style=discord.ButtonStyle.secondary, row=0, custom_id="show")
    async def show(self, interaction, _):
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)
        vc = self.get_vc(interaction)
        await vc.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message("👁 Visible", ephemeral=True)

    # ===== ROW 2 =====
    @discord.ui.button(label="👑 Claim", style=discord.ButtonStyle.primary, row=1, custom_id="claim")
    async def claim(self, interaction, _):
        vc = self.get_vc(interaction)
        data[str(vc.id)]["owner"] = interaction.user.id
        save(data)
        await interaction.response.send_message("👑 You are now owner", ephemeral=True)

    @discord.ui.button(label="👢 Kick", style=discord.ButtonStyle.danger, row=1, custom_id="kick")
    async def kick(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        await interaction.response.send_message("Select user:", view=KickView(vc), ephemeral=True)

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.secondary, row=1, custom_id="rename")
    async def rename(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        await interaction.response.send_modal(RenameModal(vc))

    @discord.ui.button(label="👥 Limit", style=discord.ButtonStyle.secondary, row=1, custom_id="limit")
    async def limit(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.check(interaction):
            return await interaction.response.send_message("❌ Not owner", ephemeral=True)

        await interaction.response.send_modal(LimitModal(vc))


# ================= COG =================

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===== AUTO VOICE =====
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        gid = str(member.guild.id)
        if gid not in data:
            return

        join_id = data[gid].get("join")

        # CREATE
        if after.channel and after.channel.id == join_id:
            vc = await member.guild.create_voice_channel(
                name=f"{member.name}",
                category=after.channel.category
            )

            await member.move_to(vc)

            data[str(vc.id)] = {"owner": member.id}
            save(data)

        # DELETE + TRANSFER
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

    # ===== AUTO SETUP =====
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def voicesetup(self, ctx):

        category = await ctx.guild.create_category("🎧 Voice")

        join = await ctx.guild.create_voice_channel("➕ Join to Create", category=category)
        panel = await ctx.guild.create_text_channel("🎛 voice-control", category=category)

        gid = str(ctx.guild.id)
        data.setdefault(gid, {})
        data[gid]["join"] = join.id
        save(data)

        embed = discord.Embed(
            title="🎛 VoiceMaster Premium",
            description="Control your voice channel using the buttons below.",
            color=discord.Color.blurple()
        )

        await panel.send(embed=embed, view=VoicePanel())

        await ctx.send("✅ Voice system fully created")


# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(Voice(bot))
