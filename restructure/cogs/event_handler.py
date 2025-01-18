import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
from utils.database import db
class EventHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @app_commands.command(name="event", description="Tạo sự kiện mới")
    @app_commands.describe(
        event_name="Tên sự kiện",
        event_datetime="Thời gian tổ chức (HH:MM DD/MM/YYYY)",
        role="Role được tham gia sự kiện",
        due_datetime="Hạn chót đăng ký (HH:MM DD/MM/YYYY)"
    )
    async def create_event(self, interaction: discord.Interaction, event_name: str, event_datetime: str, role: discord.Role, due_datetime: str):
        try:
            event_dt = datetime.datetime.strptime(event_datetime, "%H:%M %d/%m/%Y")
            due_dt = datetime.datetime.strptime(due_datetime, "%H:%M %d/%m/%Y")
        except ValueError:
            await interaction.response.send_message("Thời gian phải ở định dạng HH:MM DD/MM/YYYY", ephemeral=True)
            return

        embed = discord.Embed(title=f"Mở đăng kí tham gia sự kiện mới!", color=discord.Color.blue())
        embed.add_field(name="Sự kiện:", value=event_name, inline=False)
        embed.add_field(name="Thời gian tổ chức", value=event_datetime, inline=False)
        embed.add_field(name="Hạn chót đăng ký", value=due_datetime, inline=True)
        embed.add_field(name="Role tham gia", value=role.mention, inline=False)
        embed.add_field(name="Tham gia", value="0", inline=True)
        embed.add_field(name="Vắng mặt", value="0", inline=True)
        embed.add_field(name="Danh sách đăng kí tham gia:", value="Đang cập nhật...", inline=False)
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        query = """
        INSERT INTO events (event_name, event_datetime, role_id, due_datetime, message_id, channel_id, guild_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        event_id = db.fetch_one(query, (event_name, event_dt, role.id, due_dt, message.id, interaction.channel_id, interaction.guild_id))
        embed.set_field_at(6, name="Danh sách đăng kí tham gia:", value=f"https://gdgoc.uong.beer/event/participants/{event_id[0]}", inline=False)
        embed.set_footer(text=f"ID sự kiện: {event_id[0]}")
        
        await message.edit(embed=embed)

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        now = datetime.datetime.now()
        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)

        query_due = """
        SELECT id, event_name, due_datetime, guild_id, role_id
        FROM events
        WHERE DATE(due_datetime) BETWEEN %s AND %s
        """
        due_events = db.fetch_all(query_due, (today, tomorrow))
        for event in due_events:
            due_time = event['due_datetime'].replace(tzinfo=None)
            time_diff = due_time - now
            if datetime.timedelta(0) <= time_diff <= datetime.timedelta(hours=1):
                await self.send_due_reminder(event)

        query_event = """
        SELECT id, event_name, event_datetime, guild_id, role_id
        FROM events
        WHERE DATE(event_datetime) BETWEEN %s AND %s
        """
        upcoming_events = db.fetch_all(query_event, (today, tomorrow))
        for event in upcoming_events:
            event_time = event['event_datetime'].replace(tzinfo=None)
            time_diff = event_time - now
            if datetime.timedelta(0) <= time_diff <= datetime.timedelta(hours=1):
                await self.send_event_reminder(event)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    async def send_due_reminder(self, event):
        guild = self.bot.get_guild(event['guild_id'])
        if not guild:
            return

        role = guild.get_role(event['role_id'])
        if not role:
            return

        query_reminded = """
        SELECT user_id FROM reminders 
        WHERE event_id = %s AND reminder_type = 'due'
        """
        reminded_users = set(user['user_id'] for user in db.fetch_all(query_reminded, (event['id'],)))

        query_registered = """
        SELECT user_id FROM participants WHERE event_id = %s
        """
        registered_users = set(user['user_id'] for user in db.fetch_all(query_registered, (event['id'],)))

        users_to_remind = [member for member in role.members if member.id not in reminded_users and member.id not in registered_users]

        for user in users_to_remind:
            try:
                await user.send(f"Lời nhắc: Bạn cần đăng ký tham gia sự kiện {event['event_name']} trước {event['due_datetime'].strftime('%H:%M %d/%m/%Y')}!")
                
                q = """
                INSERT INTO reminders (event_id, user_id, reminder_type, sent_at)
                VALUES (%s, %s, 'due', %s)
                """
                db.execute_query(q, (event['id'], user.id, datetime.datetime.now()))
            except discord.Forbidden:
                pass
            except Exception:
                pass

    async def send_event_reminder(self, event):
        guild = self.bot.get_guild(event['guild_id'])
        if not guild:
            return

        query = """
        SELECT p.user_id 
        FROM participants p
        LEFT JOIN reminders r ON p.user_id = r.user_id AND r.event_id = %s AND r.reminder_type = 'event'
        WHERE p.event_id = %s AND p.status = 'going' AND r.user_id IS NULL
        """
        participants = db.fetch_all(query, (event['id'], event['id']))

        for participant in participants:
            user_id = participant['user_id']
            try:
                user = await guild.fetch_member(user_id)
                if user:
                    await user.send(f"Lời nhắc: Sự kiện {event['event_name']} sẽ diễn ra vào lúc {event['event_datetime'].strftime('%H:%M %d/%m/%Y')}, trong vòng 1 tiếng nữa. Hãy chuẩn bị kỹ càng cho sự kiện!")
                    q = """
                    INSERT INTO reminders (event_id, user_id, reminder_type, sent_at)
                    VALUES (%s, %s, 'event', %s)
                    """
                    db.execute_query(q, (event['id'], user_id, datetime.datetime.now()))
            except (discord.Forbidden, discord.NotFound, Exception):
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        query = "SELECT id, role_id FROM events WHERE message_id = %s"
        event_data = db.fetch_one(query, (payload.message_id,))

        if event_data:
            event_id, role_id = event_data
            guild = self.bot.get_guild(payload.guild_id)
            member = await guild.fetch_member(payload.user_id)
            
            if role_id not in [role.id for role in member.roles]:
                return

            status = "going" if str(payload.emoji) == "✅" else "not_going" if str(payload.emoji) == "❌" else None
            if status:
                query = """
                INSERT INTO participants (event_id, user_id, status)
                VALUES (%s, %s, %s)
                ON CONFLICT (event_id, user_id) DO UPDATE SET status = EXCLUDED.status
                """
                db.execute_query(query, (event_id, payload.user_id, status))

            await self.update_event_message(payload.message_id, event_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        query = "SELECT id FROM events WHERE message_id = %s"
        event_data = db.fetch_one(query, (payload.message_id,))

        if event_data:
            event_id = event_data[0]
            status = "going" if str(payload.emoji) == "✅" else "not_going" if str(payload.emoji) == "❌" else None
            if status:
                query = "DELETE FROM participants WHERE event_id = %s AND user_id = %s AND status = %s"
                db.execute_query(query, (event_id, payload.user_id, status))

            await self.update_event_message(payload.message_id, event_id)

    async def update_event_message(self, message_id, event_id):
        query = """
        SELECT status, COUNT(*) FROM participants
        WHERE event_id = %s GROUP BY status
        """
        participation_counts = db.fetch_all(query, (event_id,))
        going_count = next((count for status, count in participation_counts if status == 'going'), 0)
        not_going_count = next((count for status, count in participation_counts if status == 'not_going'), 0)

        channel_id_query = "SELECT channel_id FROM events WHERE id = %s"
        channel_id = db.fetch_one(channel_id_query, (event_id,))[0]
        
        channel = self.bot.get_channel(channel_id)
        if channel:
            message = await channel.fetch_message(message_id)
            embed = message.embeds[0]
            embed.set_field_at(3, name="Tham gia", value=str(going_count), inline=True)
            embed.set_field_at(4, name="Vắng mặt", value=str(not_going_count), inline=True)
            await message.edit(embed=embed)

    async def load_persisted_events(self):
        query = "SELECT id, message_id, channel_id FROM events"
        events = db.fetch_all(query)
        for event in events:
            channel = self.bot.get_channel(event['channel_id'])
            if channel:
                try:
                    message = await channel.fetch_message(event['message_id'])
                    await message.add_reaction("✅")
                    await message.add_reaction("❌")
                    await self.update_event_message(event['message_id'], event['id'])
                except discord.NotFound:
                    print(f"Không thể tìm thấy tin nhắn {event['message_id']} trong kênh {event['channel_id']}.")

async def setup(bot):
    event_handler = EventHandler(bot)
    await bot.add_cog(event_handler)
    await event_handler.load_persisted_events()