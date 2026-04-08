import discord
from discord.ext import commands
from datetime import datetime
import random
from database import db

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_imposter = {}  # {guild_id: {"active": bool, "code": str, "channel": int}}
        self.marriages = {}  # {guild_id: {user_id: married_to}}
        self.load_marriages()
        print("✅ Fun Cog geladen")

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

    def load_marriages(self):
        settings = db.get_guild_settings("global")
        if "marriages" in settings:
            self.marriages = settings["marriages"]

    def save_marriages(self):
        db.update_guild_settings("global", "marriages", self.marriages)

    # ========== 1. BODYCOUNT ==========
    @commands.command(name="bodycount")
    async def bodycount(self, ctx, member: discord.Member = None):
        """Show your or someone's body count (joke command)"""
        member = member or ctx.author
        count = random.randint(0, 999)
        embed = self.create_embed(
            "💀 Body Count",
            f"{member.mention} has a body count of **{count}**",
            0x2b2d31
        )
        await ctx.send(embed=embed)

    # ========== 2. CHEAT ==========
    @commands.command(name="cheat")
    async def cheat(self, ctx, member: discord.Member = None):
        """Cheat on someone (joke command)"""
        member = member or ctx.author
        embed = self.create_embed(
            "💔 Cheating!",
            f"{ctx.author.mention} cheated on {member.mention} with a Discord bot!",
            0xED4245
        )
        await ctx.send(embed=embed)

    # ========== 3. CRY ==========
    @commands.command(name="cry")
    async def cry(self, ctx):
        """Cry like a baby"""
        gifs = [
            "https://media.tenor.com/1TqS5Px6n8AAAAAC/anime-cry.gif",
            "https://media.tenor.com/2Xh5X5x5X5oAAAAC/anime-sad.gif",
            "https://media.tenor.com/3Yh6Y6y6Y6oAAAAC/anime-crying.gif"
        ]
        embed = self.create_embed(
            "😭 Crying",
            f"{ctx.author.mention} is crying 😢",
            0x2b2d31
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.send(embed=embed)

    # ========== 4. CUDDLE ==========
    @commands.command(name="cuddle")
    async def cuddle(self, ctx, member: discord.Member):
        """Cuddle someone"""
        gifs = [
            "https://media.tenor.com/1TqS5Px6n8AAAAAC/anime-cuddle.gif",
            "https://media.tenor.com/2Xh5X5x5X5oAAAAC/anime-hug.gif",
            "https://media.tenor.com/3Yh6Y6y6Y6oAAAAC/anime-cuddle.gif"
        ]
        embed = self.create_embed(
            "🤗 Cuddle",
            f"{ctx.author.mention} cuddles {member.mention} 🥰",
            0x57F287
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.send(embed=embed)

    # ========== 5. DIVORCE ==========
    @commands.command(name="divorce")
    async def divorce(self, ctx, member: discord.Member = None):
        """Divorce your married partner"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.marriages:
            self.marriages[guild_id] = {}
        
        if str(ctx.author.id) not in self.marriages[guild_id]:
            embed = self.create_embed("❌ Not Married", "You are not married to anyone!", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        partner_id = self.marriages[guild_id][str(ctx.author.id)]
        partner = ctx.guild.get_member(int(partner_id))
        
        del self.marriages[guild_id][str(ctx.author.id)]
        if str(partner_id) in self.marriages[guild_id]:
            del self.marriages[guild_id][str(partner_id)]
        
        self.save_marriages()
        
        embed = self.create_embed(
            "💔 Divorced",
            f"{ctx.author.mention} and {partner.mention if partner else 'someone'} are now divorced!",
            0xED4245
        )
        await ctx.send(embed=embed)

    # ========== 6. FORTUNE ==========
    @commands.command(name="fortune")
    async def fortune(self, ctx):
        """Get your fortune cookie"""
        fortunes = [
            "You will have a great day today!",
            "A surprise is waiting for you.",
            "Someone is thinking of you right now.",
            "Good fortune will come to you soon.",
            "You will meet someone interesting today.",
            "A smile will brighten your day.",
            "Your hard work will pay off.",
            "Happiness is just around the corner."
        ]
        embed = self.create_embed(
            "🥠 Fortune Cookie",
            random.choice(fortunes),
            0x57F287,
            footer=f"Requested by {ctx.author}"
        )
        await ctx.send(embed=embed)

    # ========== 7. HANDHOLD ==========
    @commands.command(name="handhold")
    async def handhold(self, ctx, member: discord.Member):
        """Hold someone's hand"""
        gifs = [
            "https://media.tenor.com/1TqS5Px6n8AAAAAC/anime-handhold.gif",
            "https://media.tenor.com/2Xh5X5x5X5oAAAAC/anime-holding-hands.gif"
        ]
        embed = self.create_embed(
            "🤝 Handhold",
            f"{ctx.author.mention} holds {member.mention}'s hand 🤝",
            0x57F287
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.send(embed=embed)

    # ========== 8. HIGHFIVE ==========
    @commands.command(name="highfive")
    async def highfive(self, ctx, member: discord.Member):
        """High five someone"""
        gifs = [
            "https://media.tenor.com/1TqS5Px6n8AAAAAC/anime-highfive.gif",
            "https://media.tenor.com/2Xh5X5x5X5oAAAAC/anime-highfive.gif"
        ]
        embed = self.create_embed(
            "🖐️ High Five",
            f"{ctx.author.mention} high fives {member.mention}!",
            0x57F287
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.send(embed=embed)

    # ========== 9. HUG ==========
    @commands.command(name="hug")
    async def hug(self, ctx, member: discord.Member):
        """Hug someone"""
        gifs = [
            "https://media.tenor.com/1TqS5Px6n8AAAAAC/anime-hug.gif",
            "https://media.tenor.com/2Xh5X5x5X5oAAAAC/anime-hug.gif",
            "https://media.tenor.com/3Yh6Y6y6Y6oAAAAC/anime-hug.gif"
        ]
        embed = self.create_embed(
            "🤗 Hug",
            f"{ctx.author.mention} hugs {member.mention} 🤗",
            0x57F287
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.send(embed=embed)

    # ========== 10. IMPOSTER-START ==========
    @commands.command(name="imposter-start")
    @commands.has_permissions(administrator=True)
    async def imposter_start(self, ctx):
        """Start an Among Us imposter game"""
        guild_id = str(ctx.guild.id)
        
        self.active_imposter[guild_id] = {
            "active": True,
            "code": "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6)),
            "channel": ctx.channel.id,
            "players": [],
            "imposter": None
        }
        
        embed = self.create_embed(
            "🎮 Among Us - Game Started!",
            f"**Game Code:** `{self.active_imposter[guild_id]['code']}`\n\n"
            "Type `!imposter-join` to join the game!\n"
            "Type `!imposter-start-game` when ready (minimum 4 players)",
            0x57F287
        )
        await ctx.send(embed=embed)

    # ========== 11. IMPOSTER-STOP ==========
    @commands.command(name="imposter-stop")
    @commands.has_permissions(administrator=True)
    async def imposter_stop(self, ctx):
        """Stop the current imposter game"""
        guild_id = str(ctx.guild.id)
        
        if guild_id in self.active_imposter and self.active_imposter[guild_id]["active"]:
            self.active_imposter[guild_id]["active"] = False
            embed = self.create_embed("🎮 Game Stopped", "The Among Us game has been stopped.", 0xED4245)
        else:
            embed = self.create_embed("❌ No Active Game", "No active Among Us game.", 0xFEE75C)
        
        await ctx.send(embed=embed)

    # ========== 12. IMPOSTER-VOTE ==========
    @commands.command(name="imposter-vote")
    async def imposter_vote(self, ctx, member: discord.Member):
        """Vote someone as imposter"""
        embed = self.create_embed(
            "🗳️ Vote Cast",
            f"{ctx.author.mention} voted for {member.mention} as imposter!",
            0xFEE75C
        )
        await ctx.send(embed=embed)

    # ========== 13. KISS ==========
    @commands.command(name="kiss")
    async def kiss(self, ctx, member: discord.Member):
        """Kiss someone"""
        gifs = [
            "https://media.tenor.com/1TqS5Px6n8AAAAAC/anime-kiss.gif",
            "https://media.tenor.com/2Xh5X5x5X5oAAAAC/anime-kiss.gif",
            "https://media.tenor.com/3Yh6Y6y6Y6oAAAAC/anime-kiss.gif"
        ]
        embed = self.create_embed(
            "💋 Kiss",
            f"{ctx.author.mention} kisses {member.mention} 💋",
            0xFF69B4
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.send(embed=embed)

    # ========== 14. LICK ==========
    @commands.command(name="lick")
    async def lick(self, ctx, member: discord.Member):
        """Lick someone"""
        gifs = [
            "https://media.tenor.com/1TqS5Px6n8AAAAAC/anime-lick.gif",
            "https://media.tenor.com/2Xh5X5x5X5oAAAAC/anime-lick.gif"
        ]
        embed = self.create_embed(
            "👅 Lick",
            f"{ctx.author.mention} licks {member.mention}!",
            0xFF69B4
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.send(embed=embed)

    # ========== 15. MARRY ==========
    @commands.command(name="marry")
    async def marry(self, ctx, member: discord.Member):
        """Marry someone"""
        if member.bot:
            embed = self.create_embed("❌ Cannot Marry", "You cannot marry a bot!", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        if member == ctx.author:
            embed = self.create_embed("❌ Cannot Marry", "You cannot marry yourself!", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.marriages:
            self.marriages[guild_id] = {}
        
        if str(ctx.author.id) in self.marriages[guild_id]:
            embed = self.create_embed("❌ Already Married", "You are already married! Divorce first.", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        if str(member.id) in self.marriages[guild_id]:
            embed = self.create_embed("❌ Already Married", f"{member.mention} is already married!", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        self.marriages[guild_id][str(ctx.author.id)] = str(member.id)
        self.marriages[guild_id][str(member.id)] = str(ctx.author.id)
        self.save_marriages()
        
        embed = self.create_embed(
            "💍 Married!",
            f"{ctx.author.mention} and {member.mention} are now married! 💍",
            0x57F287
        )
        await ctx.send(embed=embed)

    # ========== 16. MARRYSTATUS ==========
    @commands.command(name="marrystatus")
    async def marrystatus(self, ctx, member: discord.Member = None):
        """Check marriage status"""
        member = member or ctx.author
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.marriages or str(member.id) not in self.marriages[guild_id]:
            embed = self.create_embed("💍 Marriage Status", f"{member.mention} is **not married**", 0xFEE75C)
        else:
            partner_id = self.marriages[guild_id][str(member.id)]
            partner = ctx.guild.get_member(int(partner_id))
            embed = self.create_embed("💍 Marriage Status", f"{member.mention} is married to {partner.mention if partner else 'someone'}", 0x57F287)
        
        await ctx.send(embed=embed)

    # ========== 17. PP ==========
    @commands.command(name="pp")
    async def pp(self, ctx, member: discord.Member = None):
        """Measure your PP size (joke command)"""
        member = member or ctx.author
        size = random.randint(1, 20)
        bar = "=" * size + "D"
        embed = self.create_embed(
            "📏 PP Size",
            f"{member.mention}'s PP: `8{bar}` ({size}cm)",
            0x2b2d31
        )
        await ctx.send(embed=embed)

    # ========== 18. SHIP ==========
    @commands.command(name="ship")
    async def ship(self, ctx, member1: discord.Member, member2: discord.Member = None):
        """Ship two users together"""
        if not member2:
            member2 = ctx.author
        
        percentage = random.randint(0, 100)
        hearts = "❤️" * (percentage // 10) + "🖤" * (10 - percentage // 10)
        
        embed = self.create_embed(
            "💕 Ship",
            f"**{member1.display_name}** + **{member2.display_name}**\n\n{hearts}\n**{percentage}%** Match!",
            0xFF69B4
        )
        await ctx.send(embed=embed)

    # ========== 19. SLAP ==========
    @commands.command(name="slap")
    async def slap(self, ctx, member: discord.Member):
        """Slap someone"""
        gifs = [
            "https://media.tenor.com/1TqS5Px6n8AAAAAC/anime-slap.gif",
            "https://media.tenor.com/2Xh5X5x5X5oAAAAC/anime-slap.gif"
        ]
        embed = self.create_embed(
            "👋 Slap",
            f"{ctx.author.mention} slaps {member.mention}!",
            0xED4245
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.send(embed=embed)

    # ========== 20. WINK ==========
    @commands.command(name="wink")
    async def wink(self, ctx, member: discord.Member = None):
        """Wink at someone"""
        if member:
            embed = self.create_embed(
                "😉 Wink",
                f"{ctx.author.mention} winks at {member.mention}",
                0x57F287
            )
        else:
            embed = self.create_embed(
                "😉 Wink",
                f"{ctx.author.mention} winks",
                0x57F287
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
