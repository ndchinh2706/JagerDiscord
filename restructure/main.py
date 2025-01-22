import discord
from discord.ext import commands
from utils.database import db
import asyncio
from constants import Discord_API_KEY_bot
from backend.backend import app
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
import threading
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('Logged in')
    db.connect()
    await load_extensions()
    await sync_commands()

async def load_extensions():
    try:
        await bot.load_extension('cogs.event_handler')
        await bot.load_extension('cogs.signup')
        await bot.load_extension('cogs.order')
    except Exception as e:
        print(e)

async def sync_commands():
    try:
        await bot.tree.sync()
    except Exception as e:
        print(e)

async def main():
    flask_thread = threading.Thread(target=app.run)
    flask_thread.daemon = True 
    flask_thread.start()
    async with bot:
        await bot.start(Discord_API_KEY_bot)

asyncio.run(main())