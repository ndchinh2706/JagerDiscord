import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime
from constants import Discord_API_KEY_bot, db_file
import database

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="/", intents=intents)


#Database processing functions
def add_event(event_name, event_date, role_id, due_date, message_id, channel_id, guild_id):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("INSERT INTO events (event_name, event_date, role_id, due_date, message_id, channel_id, guild_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (event_name, event_date, role_id, due_date, message_id, channel_id, guild_id))
    conn.commit()
    conn.close()

def update_participant(event_id, user_id, status):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO participants (event_id, user_id, status) VALUES (?, ?, ?)",
              (event_id, user_id, status))
    conn.commit()
    conn.close()

def get_event_participation(event_id):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) FROM participants WHERE event_id = ? GROUP BY status", (event_id,))
    participation_counts = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return participation_counts

#Load các events cũ khi bot khởi động, add các reaction default.
async def load_persisted_events():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT message_id, channel_id, guild_id FROM events")
    events = c.fetchall()
    conn.close()
    for message_id, channel_id, guild_id in events:
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


#Bot event
@bot.tree.command(name="event", description="Tạo sự kiện mới")
async def create_event(interaction: discord.Interaction, 
                       event_name: str, 
                       event_date: str, 
                       role: discord.Role, 
                       due_date: str):
    
    try:
        event_dt = datetime.datetime.strptime(event_date, "%d/%m/%Y")
        due_dt = datetime.datetime.strptime(due_date, "%d/%m/%Y")
    except ValueError:
        await interaction.response.send_message("Ngày phải ở định dạng DD/MM/YYYY", ephemeral=True)
        return
    
    embed = discord.Embed(title=f"Event: {event_name}", color=discord.Color.green())
    embed.add_field(name="Ngày tổ chức", value=event_date, inline=False)
    embed.add_field(name="Hạn chót", value=due_date, inline=False)
    embed.add_field(name="Role", value=role.mention, inline=False)
    embed.add_field(name="Tham gia", value="0", inline=True)
    embed.add_field(name="Không thể tham gia", value="0", inline=True)
    
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    
    add_event(event_name, event_date, role.id, due_date, message.id, interaction.channel_id, interaction.guild.id)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT id FROM events WHERE message_id = ?", (payload.message_id,))
    event_data = c.fetchone()
    conn.close()
    
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
    print("Ready")

database.setup_database()
bot.run(Discord_API_KEY_bot)
