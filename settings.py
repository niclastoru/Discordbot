import discord
from discord.ext import commands
import json
import os

DATA_FILE = "staff_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        print("✅ Settings geladen")

    def save(self):
        save_data(self.data)

    @commands.command(name="addstaff")
    @commands.has_permissions(administrator=True)
    async def add_staff(self, ctx, role: discord.Role):
        """Add a staff role"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.data:
            self.data[guild_id] = {"staff_roles": []}
        
        if "staff_roles" not in self.data[guild_id]:
            self.data[guild_id]["staff_roles"] = []
        
        if role.id not in self.data[guild_id]["staff_roles"]:
            self.data[guild_id]["staff_roles"].append(role.id)
            self.save()
            await ctx.send(f"✅ {role.mention} wurde als Staff-Rolle hinzugefügt")
        else:
            await ctx.send(f"⚠️ {role.mention} ist bereits eine Staff-Rolle")

    @commands.command(name="removestaff")
    @commands.has_permissions(administrator=True)
    async def remove_staff(self, ctx, role: discord.Role):
        """Remove a staff role"""
        guild_id = str(ctx.guild.id)
        
        if guild_id in self.data and role.id in self.data[guild_id].get("staff_roles", []):
            self.data[guild_id]["staff_roles"].remove(role.id)
            self.save()
            await ctx.send(f"✅ {role.mention} wurde von Staff-Rollen entfernt")
        else:
            await ctx.send(f"❌ {role.mention} ist keine Staff-Rolle")

    @commands.command(name="liststaff")
    async def list_staff(self, ctx):
        """List all staff roles"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.data or not self.data[guild_id].get("staff_roles", []):
            await ctx.send("📋 Keine Staff-Rollen konfiguriert")
            return
        
        roles = [f"• <@&{r}>" for r in self.data[guild_id]["staff_roles"]]
        await ctx.send(f"**📋 Staff-Rollen:**\n" + "\n".join(roles))

    @commands.command(name="staff")
    async def show_staff(self, ctx):
        """Show online staff members"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.data or not self.data[guild_id].get("staff_roles", []):
            await ctx.send("📋 Keine Staff-Rollen konfiguriert. Nutze `!addstaff @rolle`")
            return
        
        # Alle Mitglieder mit Staff-Rollen sammeln
        staff_members = []
        for role_id in self.data[guild_id]["staff_roles"]:
            role = ctx.guild.get_role(role_id)
            if role:
                for member in role.members:
                    if member not in staff_members and not member.bot:
                        staff_members.append(member)
        
        if not staff_members:
            await ctx.send("👔 Keine Staff-Mitglieder gefunden")
            return
        
        # Online/Offline trennen
        online = []
        offline = []
        
        for member in staff_members:
            if member.status != discord.Status.offline:
                emoji = "🟢" if member.status == discord.Status.online else "🌙" if member.status == discord.Status.idle else "🔴"
                online.append(f"{emoji} {member.mention}")
            else:
                offline.append(f"⚫ {member.mention}")
        
        embed = discord.Embed(title="👔 Staff Members", color=0x2b2d31)
        
        if online:
            embed.add_field(name="🟢 Online", value="\n".join(online[:20]), inline=False)
        if offline:
            embed.add_field(name="⚫ Offline", value="\n".join(offline[:10]), inline=False)
        
        embed.set_footer(text=f"Total: {len(staff_members)} Staff")
        await ctx.send(embed=embed)

    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def set_prefix(self, ctx, new_prefix: str = None):
        """Set custom prefix for this server"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.data:
            self.data[guild_id] = {"staff_roles": []}
        
        if new_prefix is None:
            current = self.data[guild_id].get("prefix", "!")
            await ctx.send(f"📋 Aktueller Prefix: `{current}`")
            return
        
        self.data[guild_id]["prefix"] = new_prefix
        self.save()
        await ctx.send(f"✅ Prefix wurde auf `{new_prefix}` geändert")

async def setup(bot):
    await bot.add_cog(Settings(bot))
