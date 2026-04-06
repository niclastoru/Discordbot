import discord
from discord.ext import commands
from datetime import timedelta

# ================= TIME PARSER =================
def parse_time(time_str):
    try:
        unit = time_str[-1]
        value = int(time_str[:-1])

        if unit == "s":
            return timedelta(seconds=value)
        elif unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
    except:
        return None


class Moderation(commands.Cog, name="🔨 Moderation"):
    def __init__(self, bot):
        self.bot = bot

    # ================= BAN =================
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason"):
        try:
            await member.send(f"🔨 You were banned from {ctx.guild.name}\nReason: {reason}")
        except:
            pass

        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member} banned")

    # ================= UNBAN =================
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"♻️ {user} unbanned")

    # ================= KICK =================
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member} kicked")

    # ================= TIMEOUT =================
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: str):
        delta = parse_time(duration)
        if not delta:
            return await ctx.send("❌ Invalid time")

        await member.timeout(delta)
        await ctx.send(f"🔇 {member} timed out for {duration}")

    # ================= UNTIMEOUT =================
    @commands.command()
    async def untimeout(self, ctx, member: discord.Member):
        await member.timeout(None)
        await ctx.send(f"🔊 {member} untimeouted")

    # ================= PURGE =================
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Deleted {amount} messages", delete_after=3)

    # ================= CLEAR (alias purge) =================
    @commands.command()
    async def clear(self, ctx, amount: int):
        await ctx.invoke(self.purge, amount=amount)

    # ================= LOCK =================
    @commands.command()
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked")

    # ================= UNLOCK =================
    @commands.command()
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel unlocked")

    # ================= SLOWMODE =================
    @commands.command()
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"🐢 Slowmode: {seconds}s")

    # ================= NICKNAME =================
    @commands.command()
    async def nickname(self, ctx, member: discord.Member, *, name):
        await member.edit(nick=name)
        await ctx.send(f"✏️ {member} renamed")

    # ================= CLEARNICK =================
    @commands.command()
    async def clearnick(self, ctx, member: discord.Member):
        await member.edit(nick=None)
        await ctx.send(f"♻️ Nickname reset for {member}")

    # ================= ROLE =================
    @commands.command()
    async def role(self, ctx, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"➖ Removed {role} from {member}")
        else:
            await member.add_roles(role)
            await ctx.send(f"➕ Added {role} to {member}")

    # ================= ROLES =================
    @commands.command()
    async def roles(self, ctx, member: discord.Member):
        roles = ", ".join([r.name for r in member.roles if r != ctx.guild.default_role])
        await ctx.send(f"🎭 Roles: {roles}")

    # ================= MOVEALL =================
    @commands.command()
    async def moveall(self, ctx, channel: discord.VoiceChannel):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a VC first")

        for member in ctx.author.voice.channel.members:
            await member.move_to(channel)

        await ctx.send("🔁 Moved all users")

    # ================= DRAG =================
    @commands.command()
    async def drag(self, ctx, member: discord.Member):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a VC")

        await member.move_to(ctx.author.voice.channel)
        await ctx.send(f"🎯 {member} dragged")

    # ================= WARN =================
    warns = {}

    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason="No reason"):
        self.warns.setdefault(member.id, []).append(reason)
        await ctx.send(f"⚠️ {member} warned")

    # ================= HISTORY =================
    @commands.command()
    async def history(self, ctx, member: discord.Member):
        warns = self.warns.get(member.id, [])
        text = "\n".join(warns) if warns else "No warnings"
        await ctx.send(f"📜 {member}:\n{text}")

    # ================= WORD FILTER =================
    bad_words = ["badword"]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        for word in self.bad_words:
            if word in message.content.lower():
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention} watch your language")
                break


# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Moderation(bot))
