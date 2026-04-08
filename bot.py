import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- WEB-SERVER FÜR RENDER (Keep-Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot ist bereit und läuft!"

def run():
    app.run(host='0.0.0.0', port=10000) # Render nutzt oft Port 10000

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True  # WICHTIG: Im Developer Portal aktivieren!
intents.members = True          # Für Welcome-Nachrichten und Moderation

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Eingeloggt als {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="All-in-One Mode"))

# --- BEISPIEL COMMANDS ---
@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

# --- START ---
if __name__ == "__main__":
    keep_alive()  # Startet den Webserver im Hintergrund
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Fehler: Variable 'DISCORD_TOKEN' nicht in Render gefunden!")
