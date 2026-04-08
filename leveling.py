import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
from database import db

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # {user_id: last_message_time}
        self.load_levels()
        print("✅ Leveling Cog geladen")

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

    def load_levels(self):
        settings = db.get_guild_settings("global")
        if "levels" not in settings:
            settings["levels"] = {}
            db.update_guild_settings("global", "levels", {})
        self.levels = settings.get("levels", {})

    def save_levels(self):
        db.update_guild_settings("global", "levels", self.levels)

    def get_level(self, xp):
        """Calculate level from XP (Formula: 5 * level^2 + 50 * level + 100)"""
        level = 0
        while True:
            xp_needed = 5 * (level + 1) ** 2 + 50 * (level + 1) + 100
            if xp >= xp_needed:
                level += 1
            else:
                break
        return level

    def get_xp_for_level(self, level):
        """Get XP needed for a specific level"""
        return 5 * level ** 2 + 50 * level + 100

    async def add_xp(self, user_id, guild_id, amount):
        """Add XP to a user"""
        key = f"{guild_id}_{user_id}"
        if key not in self.levels:
            self.levels[key] = {"xp": 0, "level": 0}
        
        self.levels[key]["xp"] += amount
        old_level = self.levels[key]["level"]
        new_level = self.get_level(self.levels[key]["xp"])
        
        if new_level > old_level:
            self.levels[key]["level"] = new_level
            self.save_levels()
            return new_level
        
        self.save_levels()
        return None

    async def is_admin(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            embed = self.create_embed("⛔ Permission Denied", "You need `Administrator` permission.", 0xED4245)
            await ctx.send(embed=embed)
            return False
        return True

    # ========== 1. LEVEL ==========
    @commands.command(name="level")
    async def level(self, ctx, member: discord.Member = None):
        """Show your or someone's level"""
        member = member or ctx.author
        key = f"{ctx.guild.id}_{member.id}"
        
        if key not in self.levels:
            xp = 0
            level = 0
        else:
            xp = self.levels[key]["xp"]
            level = self.get_level(xp)
        
        next_level_xp = self.get_xp_for_level(level + 1)
        xp_needed = next_level_xp - xp
        xp_progress = xp - self.get_xp_for_level(level)
        xp_total_needed = next_level_xp - self.get_xp_for_level(level)
        
        progress_percent = int((xp_progress / xp_total_needed) * 100) if xp_total_needed > 0 else 0
        progress_bar = "█" * (progress_percent // 10) + "░" * (10 - progress_percent // 10)
        
        embed = self.create_embed(
            f"📊 Level - {member.display_name}",
            f"**Level:** {level}\n**XP:** {xp}/{next_level_xp}\n**Progress:** [{progress_bar}] {progress_percent}%\n\n**XP needed for next level:** {xp_needed}",
            0x57F287
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)

    # ========== 2. LEVELS STACKROLES ==========
    @commands.command(name="levels stackroles")
    @commands.has_permissions(administrator=True)
    async def levels_stackroles(self, ctx, action: str, role: discord.Role = None):
        """Stack roles (add multiple roles per level)"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        stack_roles = current.get("stack_roles", [])
        
        if action.lower() == "add" and role:
            if role.id not in stack_roles:
                stack_roles.append(role.id)
                current["stack_roles"] = stack_roles
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Stack Role Added", f"{role.mention} will stack with other level roles", 0x57F287)
            else:
                embed = self.create_embed("⚠️ Already Added", f"{role.mention} is already a stack role", 0xFEE75C)
        elif action.lower() == "remove" and role:
            if role.id in stack_roles:
                stack_roles.remove(role.id)
                current["stack_roles"] = stack_roles
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Stack Role Removed", f"{role.mention} removed from stack roles", 0x57F287)
            else:
                embed = self.create_embed("❌ Not Found", f"{role.mention} is not a stack role", 0xED4245)
        elif action.lower() == "list":
            if not stack_roles:
                embed = self.create_embed("📋 Stack Roles", "No stack roles configured", 0xFEE75C)
            else:
                roles_list = "\n".join([f"• <@&{r}>" for r in stack_roles])
                embed = self.create_embed("📋 Stack Roles", roles_list, 0x2b2d31, footer=f"Total: {len(stack_roles)}")
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add`, `remove`, or `list`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 3. LEVELS-ADD ==========
    @commands.command(name="levels-add")
    @commands.has_permissions(administrator=True)
    async def levels_add(self, ctx, member: discord.Member, amount: int):
        """Add XP to a member"""
        if amount < 0:
            embed = self.create_embed("❌ Invalid Amount", "Amount must be positive", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        key = f"{ctx.guild.id}_{member.id}"
        if key not in self.levels:
            self.levels[key] = {"xp": 0, "level": 0}
        
        self.levels[key]["xp"] += amount
        new_level = self.get_level(self.levels[key]["xp"])
        
        if new_level > self.levels[key]["level"]:
            self.levels[key]["level"] = new_level
        
        self.save_levels()
        embed = self.create_embed("✅ XP Added", f"Added **{amount} XP** to {member.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 4. LEVELS-CLEANUP ==========
    @commands.command(name="levels-cleanup")
    @commands.has_permissions(administrator=True)
    async def levels_cleanup(self, ctx):
        """Clean up levels data for users who left"""
        count = 0
        to_delete = []
        
        for key in self.levels:
            guild_id, user_id = key.split("_")
            if int(guild_id) == ctx.guild.id:
                member = ctx.guild.get_member(int(user_id))
                if not member:
                    to_delete.append(key)
                    count += 1
        
        for key in to_delete:
            del self.levels[key]
        
        self.save_levels()
        embed = self.create_embed("✅ Cleanup Complete", f"Removed **{count}** users who left the server", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 5. LEVELS-IGNORE ==========
    @commands.command(name="levels-ignore")
    @commands.has_permissions(administrator=True)
    async def levels_ignore(self, ctx, action: str, channel: discord.TextChannel = None):
        """Ignore a channel for leveling"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        ignored = current.get("ignored_channels", [])
        
        if not channel:
            embed = self.create_embed("❌ Missing Channel", "Usage: `!levels-ignore add #channel` or `!levels-ignore remove #channel`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        if action.lower() == "add":
            if channel.id in ignored:
                embed = self.create_embed("⚠️ Already Ignored", f"{channel.mention} is already ignored", 0xFEE75C)
            else:
                ignored.append(channel.id)
                current["ignored_channels"] = ignored
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Channel Ignored", f"{channel.mention} will no longer give XP", 0x57F287)
        elif action.lower() == "remove":
            if channel.id in ignored:
                ignored.remove(channel.id)
                current["ignored_channels"] = ignored
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Channel Unignored", f"{channel.mention} will now give XP again", 0x57F287)
            else:
                embed = self.create_embed("❌ Not Ignored", f"{channel.mention} is not ignored", 0xED4245)
        else:
            embed = self.create_embed("❌ Invalid Action", "Use `add` or `remove`", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 6. LEVELS-LEADERBOARD ==========
    @commands.command(name="levels-leaderboard", aliases=["lb", "leaderboard"])
    async def levels_leaderboard(self, ctx, page: int = 1):
        """Show XP leaderboard"""
        guild_data = []
        for key, data in self.levels.items():
            guild_id, user_id = key.split("_")
            if int(guild_id) == ctx.guild.id:
                guild_data.append((int(user_id), data["xp"]))
        
        if not guild_data:
            embed = self.create_embed("📊 Leaderboard", "No XP data yet. Start chatting!", 0xFEE75C)
            await ctx.send(embed=embed)
            return
        
        guild_data.sort(key=lambda x: x[1], reverse=True)
        
        items_per_page = 10
        total_pages = (len(guild_data) + items_per_page - 1) // items_per_page
        
        if page < 1 or page > total_pages:
            page = 1
        
        start = (page - 1) * items_per_page
        end = start + items_per_page
        page_data = guild_data[start:end]
        
        leaderboard_text = ""
        for i, (user_id, xp) in enumerate(page_data, start=start + 1):
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else f"Unknown ({user_id})"
            level = self.get_level(xp)
            leaderboard_text += f"**{i}.** {name} - Level {level} ({xp} XP)\n"
        
        embed = self.create_embed(
            f"📊 XP Leaderboard - Page {page}/{total_pages}",
            leaderboard_text,
            0x57F287
        )
        await ctx.send(embed=embed)

    # ========== 7. LEVELS-LOCK ==========
    @commands.command(name="levels-lock")
    @commands.has_permissions(administrator=True)
    async def levels_lock(self, ctx):
        """Lock leveling system (stop XP gain)"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        current["leveling_locked"] = True
        db.update_guild_settings(ctx.guild.id, "settings", current)
        
        embed = self.create_embed("🔒 Leveling Locked", "No more XP will be awarded until unlocked", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 8. LEVELS-MESSAGEMODE ==========
    @commands.command(name="levels-messageMode")
    @commands.has_permissions(administrator=True)
    async def levels_message_mode(self, ctx, mode: str):
        """Set level up message mode: dm, channel, or off"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        
        if mode.lower() not in ["dm", "channel", "off"]:
            embed = self.create_embed("❌ Invalid Mode", "Use `dm`, `channel`, or `off`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        current["levelup_mode"] = mode.lower()
        db.update_guild_settings(ctx.guild.id, "settings", current)
        
        embed = self.create_embed("✅ Message Mode Set", f"Level up messages will be sent via **{mode}**", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 9. LEVELS-REMOVE ==========
    @commands.command(name="levels-remove")
    @commands.has_permissions(administrator=True)
    async def levels_remove(self, ctx, member: discord.Member, amount: int):
        """Remove XP from a member"""
        if amount < 0:
            embed = self.create_embed("❌ Invalid Amount", "Amount must be positive", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        key = f"{ctx.guild.id}_{member.id}"
        if key not in self.levels:
            self.levels[key] = {"xp": 0, "level": 0}
        
        self.levels[key]["xp"] = max(0, self.levels[key]["xp"] - amount)
        self.levels[key]["level"] = self.get_level(self.levels[key]["xp"])
        self.save_levels()
        
        embed = self.create_embed("✅ XP Removed", f"Removed **{amount} XP** from {member.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 10. LEVELS-RESET ==========
    @commands.command(name="levels-reset")
    @commands.has_permissions(administrator=True)
    async def levels_reset(self, ctx, member: discord.Member = None):
        """Reset XP for a member or entire server"""
        if member:
            key = f"{ctx.guild.id}_{member.id}"
            if key in self.levels:
                del self.levels[key]
            self.save_levels()
            embed = self.create_embed("✅ XP Reset", f"Reset XP for {member.mention}", 0x57F287)
        else:
            # Reset entire server
            to_delete = []
            for key in self.levels:
                guild_id, _ = key.split("_")
                if int(guild_id) == ctx.guild.id:
                    to_delete.append(key)
            for key in to_delete:
                del self.levels[key]
            self.save_levels()
            embed = self.create_embed("✅ Server XP Reset", f"Reset XP for all **{len(to_delete)}** users", 0x57F287)
        
        await ctx.send(embed=embed)

    # ========== 11. LEVELS-ROLES ==========
    @commands.command(name="levels-roles")
    @commands.has_permissions(administrator=True)
    async def levels_roles(self, ctx, level: int, role: discord.Role = None):
        """Set role rewards for specific levels"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        level_roles = current.get("level_roles", {})
        
        if role:
            level_roles[str(level)] = role.id
            current["level_roles"] = level_roles
            db.update_guild_settings(ctx.guild.id, "settings", current)
            embed = self.create_embed("✅ Level Role Set", f"Level **{level}** → {role.mention}", 0x57F287)
        else:
            if str(level) in level_roles:
                del level_roles[str(level)]
                current["level_roles"] = level_roles
                db.update_guild_settings(ctx.guild.id, "settings", current)
                embed = self.create_embed("✅ Level Role Removed", f"Removed reward for level **{level}**", 0x57F287)
            else:
                embed = self.create_embed("❌ No Role Found", f"No role reward for level **{level}**", 0xED4245)
        await ctx.send(embed=embed)

    # ========== 12. LEVELS-SETRATE ==========
    @commands.command(name="levels-setrate")
    @commands.has_permissions(administrator=True)
    async def levels_setrate(self, ctx, min_xp: int, max_xp: int, cooldown: int):
        """Set XP rate (min, max, cooldown in seconds)"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        
        if min_xp < 1 or max_xp < min_xp or cooldown < 1:
            embed = self.create_embed("❌ Invalid Values", "Min XP ≥ 1, Max XP ≥ Min XP, Cooldown ≥ 1", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        current["xp_rate"] = {"min": min_xp, "max": max_xp, "cooldown": cooldown}
        db.update_guild_settings(ctx.guild.id, "settings", current)
        
        embed = self.create_embed("✅ XP Rate Set", f"**Min:** {min_xp}\n**Max:** {max_xp}\n**Cooldown:** {cooldown}s", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 13. LEVELS-SYNC ==========
    @commands.command(name="levels-sync")
    @commands.has_permissions(administrator=True)
    async def levels_sync(self, ctx):
        """Sync level roles for all members"""
        settings = db.get_guild_settings(ctx.guild.id)
        level_roles = settings.get("settings", {}).get("level_roles", {})
        
        if not level_roles:
            embed = self.create_embed("❌ No Level Roles", "Set level roles first with `!levels-roles`", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        count = 0
        for key, data in self.levels.items():
            guild_id, user_id = key.split("_")
            if int(guild_id) == ctx.guild.id:
                member = ctx.guild.get_member(int(user_id))
                if member:
                    level = self.get_level(data["xp"])
                    for lvl, role_id in level_roles.items():
                        role = ctx.guild.get_role(role_id)
                        if role and int(lvl) <= level and role not in member.roles:
                            await member.add_roles(role)
                            count += 1
        
        embed = self.create_embed("✅ Sync Complete", f"Added **{count}** level roles to members", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 14. LEVELS-UNLOCK ==========
    @commands.command(name="levels-unlock")
    @commands.has_permissions(administrator=True)
    async def levels_unlock(self, ctx):
        """Unlock leveling system (allow XP gain)"""
        settings = db.get_guild_settings(ctx.guild.id)
        current = settings.get("settings", {})
        current["leveling_locked"] = False
        db.update_guild_settings(ctx.guild.id, "settings", current)
        
        embed = self.create_embed("🔓 Leveling Unlocked", "XP gain has been re-enabled", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 15. LEVELS-UPDATE ==========
    @commands.command(name="levels-update")
    @commands.has_permissions(administrator=True)
    async def levels_update(self, ctx, member: discord.Member):
        """Update level roles for a specific member"""
        settings = db.get_guild_settings(ctx.guild.id)
        level_roles = settings.get("settings", {}).get("level_roles", {})
        
        key = f"{ctx.guild.id}_{member.id}"
        if key not in self.levels:
            embed = self.create_embed("❌ No Data", f"{member.mention} has no XP data", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        level = self.get_level(self.levels[key]["xp"])
        count = 0
        
        for lvl, role_id in level_roles.items():
            role = ctx.guild.get_role(role_id)
            if role and int(lvl) <= level:
                if role not in member.roles:
                    await member.add_roles(role)
                    count += 1
        
        embed = self.create_embed("✅ Roles Updated", f"Added **{count}** level roles to {member.mention}", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 16. LEVELS (alias) ==========
    # Already have level command as #1

    # ========== 17. REMOVEXP ==========
    @commands.command(name="removexp")
    @commands.has_permissions(administrator=True)
    async def removexp(self, ctx, member: discord.Member, amount: int):
        """Remove XP from a member (alias for levels-remove)"""
        await self.levels_remove(ctx, member, amount)

    # ========== 18. SETLEVEL ==========
    @commands.command(name="setlevel")
    @commands.has_permissions(administrator=True)
    async def setlevel(self, ctx, member: discord.Member, level: int):
        """Set a member's level directly"""
        if level < 0:
            embed = self.create_embed("❌ Invalid Level", "Level must be 0 or higher", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        required_xp = self.get_xp_for_level(level)
        key = f"{ctx.guild.id}_{member.id}"
        
        if key not in self.levels:
            self.levels[key] = {"xp": 0, "level": 0}
        
        self.levels[key]["xp"] = required_xp
        self.levels[key]["level"] = level
        self.save_levels()
        
        embed = self.create_embed("✅ Level Set", f"Set {member.mention} to level **{level}**", 0x57F287)
        await ctx.send(embed=embed)

    # ========== 19. SETXP ==========
    @commands.command(name="setxp")
    @commands.has_permissions(administrator=True)
    async def setxp(self, ctx, member: discord.Member, xp: int):
        """Set a member's XP directly"""
        if xp < 0:
            embed = self.create_embed("❌ Invalid XP", "XP must be 0 or higher", 0xED4245)
            await ctx.send(embed=embed)
            return
        
        key = f"{ctx.guild.id}_{member.id}"
        
        if key not in self.levels:
            self.levels[key] = {"xp": 0, "level": 0}
        
        self.levels[key]["xp"] = xp
        self.levels[key]["level"] = self.get_level(xp)
        self.save_levels()
        
        embed = self.create_embed("✅ XP Set", f"Set {member.mention} to **{xp} XP** (Level {self.levels[key]['level']})", 0x57F287)
        await ctx.send(embed=embed)

    # ========== XP GAIN LISTENER ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        # Check if leveling is locked
        settings = db.get_guild_settings(message.guild.id)
        if settings.get("settings", {}).get("leveling_locked", False):
            return
        
        # Check ignored channels
        ignored = settings.get("settings", {}).get("ignored_channels", [])
        if message.channel.id in ignored:
            return
        
        # Cooldown check
        user_id = str(message.author.id)
        now = datetime.utcnow()
        
        if user_id in self.cooldowns:
            rate_settings = settings.get("settings", {}).get("xp_rate", {"cooldown": 60})
            cooldown_seconds = rate_settings.get("cooldown", 60)
            if (now - self.cooldowns[user_id]).total_seconds() < cooldown_seconds:
                return
        
        self.cooldowns[user_id] = now
        
        # Get XP rate
        rate = settings.get("settings", {}).get("xp_rate", {"min": 10, "max": 20})
        xp_gain = random.randint(rate.get("min", 10), rate.get("max", 20))
        
        # Add XP
        new_level = await self.add_xp(message.author.id, message.guild.id, xp_gain)
        
        # Level up message
        if new_level:
            levelup_mode = settings.get("settings", {}).get("levelup_mode", "channel")
            
            embed = self.create_embed(
                "🎉 Level Up! 🎉",
                f"{message.author.mention} reached **Level {new_level}**!",
                0x57F287
            )
            
            if levelup_mode == "dm":
                try:
                    await message.author.send(embed=embed)
                except:
                    pass
            elif levelup_mode == "channel":
                await message.channel.send(embed=embed)
            
            # Give level roles
            level_roles = settings.get("settings", {}).get("level_roles", {})
            for lvl, role_id in level_roles.items():
                if int(lvl) <= new_level:
                    role = message.guild.get_role(role_id)
                    if role and role not in message.author.roles:
                        await message.author.add_roles(role)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
