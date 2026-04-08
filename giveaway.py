import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timedelta
import asyncio
import random
from database import db

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}  # {channel_id: {message_id: giveaway_data}}
        print("✅ Giveaway Cog geladen")

    def create_embed(self, title, description, color, fields=None, footer=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        if footer:
            embed.set_footer(text=footer)
        return embed

    async def is_admin(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            embed = self.create_embed("⛔ Permission Denied", "You need `Administrator` permission.", 0xED4245)
            await ctx.send(embed=embed)
            return False
        return True

    # ========== 1. GETID ==========
    @commands.command(name="getid")
    @commands.has_permissions(administrator=True)
    async def getid(self, ctx, *, name: str = None):
        """Get user ID by name or mention"""
        if not name:
            embed = self.create_embed("❌ Missing Name", "Usage: `!getid @user` or `!getid username`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        # Try to get member
        member = None
        
        # Try mention
        if len(ctx.message.mentions) > 0:
            member = ctx.message.mentions[0]
        else:
            # Try by name
            for m in ctx.guild.members:
                if m.name.lower() == name.lower() or m.display_name.lower() == name.lower():
                    member = m
                    break
        
        if member:
            embed = self.create_embed("🆔 User ID", f"{member.mention}\n**ID:** `{member.id}`", 0x57F287)
        else:
            embed = self.create_embed("❌ User Not Found", f"Could not find user `{name}`", 0xED4245)
        
        await ctx.send(embed=embed)

    # ========== 2. GEND (End Giveaway) ==========
    @commands.command(name="gend")
    @commands.has_permissions(administrator=True)
    async def gend(self, ctx, message_id: int):
        """End a giveaway early"""
        # Find giveaway
        giveaway_data = None
        for g_data in self.active_giveaways.values():
            if str(message_id) in g_data:
                giveaway_data = g_data[str(message_id)]
                break
        
        if not giveaway_data:
            embed = self.create_embed("❌ Giveaway Not Found", f"No active giveaway with ID `{message_id}`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        # End giveaway
        channel = self.bot.get_channel(giveaway_data["channel_id"])
        if channel:
            try:
                message = await channel.fetch_message(message_id)
                
                # Get participants
                participants = []
                for reaction in message.reactions:
                    if str(reaction.emoji) == "🎉":
                        async for user in reaction.users():
                            if not user.bot:
                                participants.append(user)
                        break
                
                # Pick winner
                if participants:
                    winner = random.choice(participants)
                    winner_text = winner.mention
                else:
                    winner_text = "No participants"
                
                # Update embed
                embed = discord.Embed(
                    title="🎉 GIVEAWAY ENDED 🎉",
                    description=f"**Prize:** {giveaway_data['prize']}\n**Winner:** {winner_text}",
                    color=0xED4245,
                    timestamp=datetime.utcnow()
                )
                await message.edit(embed=embed, view=None)
                await channel.send(f"🎉 Giveaway ended! Winner: {winner_text}")
                
            except:
                pass
        
        # Remove from active
        del self.active_giveaways[giveaway_data["channel_id"]][str(message_id)]
        
        embed = self.create_embed("✅ Giveaway Ended", f"Giveaway `{message_id}` has been ended", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 3. GLIST (List Giveaways) ==========
    @commands.command(name="glist")
    @commands.has_permissions(administrator=True)
    async def glist(self, ctx):
        """List all active giveaways"""
        if not self.active_giveaways:
            embed = self.create_embed("📋 Active Giveaways", "No active giveaways.", 0xFEE75C)
            await ctx.send(embed=embed)
            return
        
        giveaway_list = []
        for channel_id, giveaways in self.active_giveaways.items():
            channel = self.bot.get_channel(int(channel_id))
            for msg_id, data in giveaways.items():
                end_time = datetime.fromisoformat(data["end_time"])
                giveaway_list.append(f"• {channel.mention if channel else 'Unknown'} | `{msg_id}` | {data['prize']} | Ends: <t:{int(end_time.timestamp())}:R>")
        
        embed = self.create_embed("📋 Active Giveaways", "\n".join(giveaway_list) if giveaway_list else "None", 0x2b2d31, footer=f"Total: {len(giveaway_list)}")
        await ctx.send(embed=embed)

    # ========== 4. GREROLL (Reroll Giveaway) ==========
    @commands.command(name="greroll")
    @commands.has_permissions(administrator=True)
    async def greroll(self, ctx, message_id: int):
        """Reroll a giveaway winner"""
        # Try to find giveaway
        channel = ctx.channel
        try:
            message = await channel.fetch_message(message_id)
            
            # Get participants
            participants = []
            for reaction in message.reactions:
                if str(reaction.emoji) == "🎉":
                    async for user in reaction.users():
                        if not user.bot:
                            participants.append(user)
                    break
            
            if not participants:
                embed = self.create_embed("❌ No Participants", "No valid participants found for this giveaway", 0xED4245)
                await ctx.send(embed=embed)
                return
            
            winner = random.choice(participants)
            embed = self.create_embed("🎉 Giveaway Rerolled", f"New winner: {winner.mention}", 0x57F287)
            await ctx.send(embed=embed)
            await channel.send(f"🎉 New winner for giveaway `{message_id}`: {winner.mention}")
            
        except discord.NotFound:
            embed = self.create_embed("❌ Message Not Found", f"Could not find message `{message_id}` in this channel", 0xED4245)
            await ctx.send(embed=embed)

    # ========== 5. GSTART (Start Giveaway) ==========
    @commands.command(name="gstart")
    @commands.has_permissions(administrator=True)
    async def gstart(self, ctx, duration: str, winners: int, *, prize: str):
        """Start a giveaway. Usage: !gstart 1h 1 Nitro or !gstart 30m 3 Discord Nitro"""
        
        # Parse duration
        total_seconds = 0
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        
        import re
        matches = re.findall(r'(\d+)([smhd])', duration.lower())
        if not matches:
            embed = self.create_embed("❌ Invalid Duration", "Use format like `10m`, `1h30m`, `2h`, `30s`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        for value, unit in matches:
            total_seconds += int(value) * time_units[unit]
        
        if total_seconds < 10 or total_seconds > 604800:
            embed = self.create_embed("❌ Invalid Duration", "Duration must be between 10 seconds and 7 days", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        if winners < 1 or winners > 10:
            embed = self.create_embed("❌ Invalid Winners", "Winners must be between 1 and 10", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        end_time = datetime.utcnow() + timedelta(seconds=total_seconds)
        
        # Create giveaway embed
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Hosted by:** {ctx.author.mention}\n\nReact with 🎉 to enter!",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Ends", value=f"<t:{int(end_time.timestamp())}:R> (<t:{int(end_time.timestamp())}:F>)", inline=False)
        embed.set_footer(text=f"Giveaway ID: {ctx.message.id}")
        
        # Send message
        giveaway_msg = await ctx.send(embed=embed)
        await giveaway_msg.add_reaction("🎉")
        
        # Save to active giveaways
        if str(ctx.channel.id) not in self.active_giveaways:
            self.active_giveaways[str(ctx.channel.id)] = {}
        
        self.active_giveaways[str(ctx.channel.id)][str(giveaway_msg.id)] = {
            "prize": prize,
            "winners": winners,
            "host": str(ctx.author.id),
            "end_time": end_time.isoformat(),
            "channel_id": ctx.channel.id,
            "message_id": giveaway_msg.id
        }
        
        embed = self.create_embed("✅ Giveaway Started", f"Prize: **{prize}**\nEnds: <t:{int(end_time.timestamp())}:R>\nChannel: {ctx.channel.mention}", 0x57F287)
        await ctx.send(embed=embed)
        
        # Wait for giveaway to end
        await asyncio.sleep(total_seconds)
        
        # Check if still active
        if str(giveaway_msg.id) in self.active_giveaways.get(str(ctx.channel.id), {}):
            # Fetch message and get participants
            try:
                msg = await ctx.channel.fetch_message(giveaway_msg.id)
                
                # Get participants
                participants = []
                for reaction in msg.reactions:
                    if str(reaction.emoji) == "🎉":
                        async for user in reaction.users():
                            if not user.bot:
                                participants.append(user)
                        break
                
                # Pick winners
                if len(participants) >= winners:
                    winners_list = random.sample(participants, winners)
                    winner_text = ", ".join([w.mention for w in winners_list])
                else:
                    winner_text = "Not enough participants"
                
                # Update embed
                end_embed = discord.Embed(
                    title="🎉 GIVEAWAY ENDED 🎉",
                    description=f"**Prize:** {prize}\n**Winners:** {winner_text}",
                    color=0xED4245,
                    timestamp=datetime.utcnow()
                )
                await msg.edit(embed=end_embed)
                await ctx.channel.send(f"🎉 Giveaway ended! Winners: {winner_text}")
                
            except:
                pass
            
            # Remove from active
            del self.active_giveaways[str(ctx.channel.id)][str(giveaway_msg.id)]

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
