import discord
from discord.ext import commands
import random
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=",", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

@bot.command()
async def ship(ctx, member: discord.Member):
    love = random.randint(0, 100)
    await ctx.send(
        f"💖 {ctx.author.display_name} × {member.display_name} = **{love}% Liebe**"
    )

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send("❌ Rolle nicht gefunden.")
        return

    await member.add_roles(role)
    await ctx.send(f"✅ Rolle **{role.name}** wurde {member.display_name} gegeben.")

bot.run(os.environ["TOKEN"])
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if reason is None:
        reason = "Kein Grund angegeben"

    try:
        await member.ban(reason=reason)
        await ctx.send(
            f"🔨 **{member}** wurde gebannt.\n📄 **Grund:** {reason}"
        )
    except discord.Forbidden:
        await ctx.send("❌ Ich habe keine Rechte, diesen User zu bannen.")
    except discord.HTTPException:
        await ctx.send("❌ Fehler beim Bannen.")
@bot.command()
@commands.has_permissions(moderate_members=True)
async def jail(ctx, member: discord.Member, *, reason="Kein Grund angegeben"):
    jail_role = discord.utils.get(ctx.guild.roles, name="jailed")

    if not jail_role:
        await ctx.send("❌ Jail-Rolle existiert nicht.")
        return

    if jail_role in member.roles:
        await ctx.send("⚠️ User ist bereits im Jail.")
        return

    await member.add_roles(jail_role, reason=reason)
    await ctx.send(f"🔒 {member.mention} wurde gejailt.\n📝 Grund: **{reason}**")
@bot.command()
@commands.has_permissions(moderate_members=True)
async def unjail(ctx, member: discord.Member):
    jail_role = discord.utils.get(ctx.guild.roles, name="jailed")

    if not jail_role:
        await ctx.send("❌ Jail-Rolle existiert nicht.")
        return

    if jail_role not in member.roles:
        await ctx.send("⚠️ User ist nicht im Jail.")
        return

    await member.remove_roles(jail_role)
    await ctx.send(f"🔓 {member.mention} wurde entjailt.")
# --- MARRIAGE SYSTEM ---

marriages = {}        # user_id -> partner_id
pending_proposals = {}  # target_id -> proposer_id

@bot.command()
async def marry(ctx, member: discord.Member):
    author = ctx.author

    if author.id == member.id:
        await ctx.send("❌ Du kannst dich nicht selbst heiraten.")
        return

    if author.id in marriages:
        await ctx.send("❌ Du bist bereits verheiratet.")
        return

    if member.id in marriages:
        await ctx.send("❌ Diese Person ist bereits verheiratet.")
        return

    pending_proposals[member.id] = author.id
    await ctx.send(
        f"💍 {member.mention}, {author.mention} möchte dich heiraten!\n"
        f"Schreibe **,accept** oder **,decline**"
    )

@bot.command()
async def accept(ctx):
    target = ctx.author

    if target.id not in pending_proposals:
        await ctx.send("❌ Du hast keine offene Anfrage.")
        return

    proposer_id = pending_proposals.pop(target.id)

    marriages[target.id] = proposer_id
    marriages[proposer_id] = target.id

    proposer = ctx.guild.get_member(proposer_id)
    await ctx.send(f"💖 {target.mention} und {proposer.mention} sind jetzt verheiratet!")

@bot.command()
async def decline(ctx):
    target = ctx.author

    if target.id not in pending_proposals:
        await ctx.send("❌ Du hast keine offene Anfrage.")
        return

    proposer_id = pending_proposals.pop(target.id)
    proposer = ctx.guild.get_member(proposer_id)

    await ctx.send(f"💔 {target.mention} hat den Antrag von {proposer.mention} abgelehnt.")

@bot.command()
async def divorce(ctx):
    author = ctx.author

    if author.id not in marriages:
        await ctx.send("❌ Du bist nicht verheiratet.")
        return

    partner_id = marriages.pop(author.id)
    marriages.pop(partner_id, None)

    partner = ctx.guild.get_member(partner_id)
    await ctx.send(f"💔 {author.mention} und {partner.mention} sind jetzt geschieden.")
@bot.command()
async def marrystatus(ctx, member: discord.Member = None):
    user = member or ctx.author

    if user.id not in marriages:
        await ctx.send(f"💔 {user.mention} ist nicht verheiratet.")
        return

    partner_id = marriages[user.id]
    partner = ctx.guild.get_member(partner_id)

    await ctx.send(
        f"💍 **Marriage Status**\n"
        f"👤 {user.mention}\n"
        f"❤️ Verheiratet mit: {partner.mention}"
    )
