import discord
from discord.ext import commands
import sqlite3
import datetime
from constants import Discord_API_KEY_bot, DB_Name, DB_User, DB_Pass, DB_Host, DB_Port
import database
import psycopg2

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="/", intents=intents)

conn = psycopg2.connect(
    dbname=DB_Name,
    user=DB_User,
    password=DB_Pass,
    host=DB_Host,  
    port=DB_Port   
)

def add_event(event_name, event_date, role_id, due_date, message_id, channel_id, guild_id):
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (event_name, event_date, role_id, due_date, message_id, channel_id, guild_id) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (event_name, event_date, role_id, due_date, message_id, channel_id, guild_id)
    )
    event_id = c.fetchone()[0]  # Lấy ID của sự kiện vừa tạo
    conn.commit()
    return event_id

def update_participant(event_id, user_id, status):
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO participants (event_id, user_id, status)
        VALUES (%s, %s, %s)
        ON CONFLICT (event_id, user_id)
        DO UPDATE SET status = EXCLUDED.status
        """,
        (event_id, user_id, status)
    )
    conn.commit()

def get_event_participation(event_id):
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) FROM participants WHERE event_id = %s GROUP BY status", (event_id,))
    participation_counts = {row[0]: row[1] for row in c.fetchall()}
    return participation_counts

async def load_persisted_events():
    c = conn.cursor()
    c.execute("SELECT message_id, channel_id, guild_id FROM events")
    events = c.fetchall()
    for event_id, message_id, channel_id, guild_id in events:
        guild = bot.get_guild(guild_id)
        if guild:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    await message.add_reaction("✅")
                    await message.add_reaction("❌")
                except (discord.NotFound, discord.Forbidden):
                    print(f"Không thể tìm thấy tin nhắn {message_id} trong kênh {channel_id}.")

# Lệnh bot để tạo sự kiện mới
@bot.tree.command(name="event", description="Tạo sự kiện mới")
async def create_event(interaction: discord.Interaction, event_name: str, event_date: str, role: discord.Role, due_date: str):
    try:
        event_dt = datetime.datetime.strptime(event_date, "%d/%m/%Y")
        due_dt = datetime.datetime.strptime(due_date, "%d/%m/%Y")
    except ValueError:
        await interaction.response.send_message("Ngày phải ở định dạng DD/MM/YYYY", ephemeral=True)
        return

    embed = discord.Embed(title=f"Sự kiện: {event_name}", color=discord.Color.green())
    embed.add_field(name="Ngày tổ chức", value=event_date, inline=False)
    embed.add_field(name="Hạn chót", value=due_date, inline=False)
    embed.add_field(name="Vai trò", value=role.mention, inline=False)
    embed.add_field(name="Tham gia", value="0", inline=True)
    embed.add_field(name="Không thể tham gia", value="0", inline=True)

    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    event_id = add_event(event_name, event_date, role.id, due_date, message.id, interaction.channel_id, interaction.guild.id)
    embed.set_footer(text=f"ID sự kiện: {event_id}")
    await message.edit(embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    c = conn.cursor()
    c.execute("SELECT id FROM events WHERE message_id = %s", (payload.message_id,))
    event_data = c.fetchone()

    if event_data:
        event_id = event_data[0]
        status = "going" if payload.emoji.name == "✅" else "not_going" if payload.emoji.name == "❌" else None
        if status:
            update_participant(event_id, payload.user_id, status)

        participation_counts = get_event_participation(event_id)
        going_count = participation_counts.get("going", 0)
        not_going_count = participation_counts.get("not_going", 0)

        guild = bot.get_guild(payload.guild_id)
        if guild:
            channel = guild.get_channel(payload.channel_id)
            if channel:
                message = await channel.fetch_message(payload.message_id)
                embed = message.embeds[0]
                embed.set_field_at(3, name="Tham gia", value=str(going_count), inline=True)
                embed.set_field_at(4, name="Không thể tham gia", value=str(not_going_count), inline=True)
                await message.edit(embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync()
    await load_persisted_events()
    print("Bot đã sẵn sàng.")

database.setup_database()
bot.run(Discord_API_KEY_bot)
