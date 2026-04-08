import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- WEB SERVER FÜR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot ist online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- DISCORD BOT LOGIK ---
intents = discord.Intents.default()
intents.message_content = True  # Wichtig für Commands!

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Eingeloggt als {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! Latenz: {round(bot.latency * 1000)}ms')

# --- START ---
if __name__ == "__main__":
    keep_alive()  # Startet den Webserver
    # Den Token ziehen wir sicher aus den Environment Variables von Render
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Fehler: Kein DISCORD_TOKEN gefunden!")
