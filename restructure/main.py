import discord
from discord.ext import commands
from config import BOT_TOKEN
from utils.database import db
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Đã đăng nhập với tên {bot.user.name}')
    db.connect()
    await load_extensions()
    await sync_commands()

async def load_extensions():
    try:
        await bot.load_extension('cogs.event_handler')
        await bot.load_extension('cogs.signup')

        print("Đã tải extension event_handler")
    except Exception as e:
        print(f"Lỗi khi tải extension event_handler: {e}")

async def sync_commands():
    try:
        print("Đang đồng bộ hóa commands...")
        await bot.tree.sync()
        print("Đã đồng bộ hóa commands thành công")
    except Exception as e:
        print(f"Lỗi khi đồng bộ hóa commands: {e}")

@bot.event
async def on_disconnect():
    db.disconnect()
    print("Bot đã ngắt kết nối")

async def main():
    async with bot:
        await bot.start(BOT_TOKEN)

asyncio.run(main())