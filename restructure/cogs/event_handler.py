import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
from utils.database import db

def has_required_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        allowed_role_names = ["Admin"]
        if not any(discord.utils.get(interaction.user.roles, name=role_name) for role_name in allowed_role_names):
            await interaction.response.send_message(f"Bạn cần có một trong các role sau để sử dụng lệnh này: {', '.join(allowed_role_names)}", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

class EventHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @app_commands.command(name="event", description="Tạo sự kiện mới")
    @app_commands.describe(
        event_name="Tên sự kiện",
        event_datetime="Thời gian tổ chức (HH:MM DD/MM/YYYY)",
        role1="Role được tham gia sự kiện 1",
        role2="Role được tham gia sự kiện 2 (không bắt buộc)",
        role3="Role được tham gia sự kiện 3 (không bắt buộc)",
        due_datetime="Hạn chót đăng ký (HH:MM DD/MM/YYYY)"
    )
    @has_required_role()
    async def create_event(
        self, 
        interaction: discord.Interaction, 
        event_name: str, 
        event_datetime: str, 
        due_datetime: str,
        role1: discord.Role,
        role2: discord.Role = None,
        role3: discord.Role = None
    ):
        try:
            event_dt = datetime.datetime.strptime(event_datetime, "%H:%M %d/%m/%Y")
            due_dt = datetime.datetime.strptime(due_datetime, "%H:%M %d/%m/%Y")
        except ValueError:
            await interaction.response.send_message("Thời gian phải ở định dạng HH:MM DD/MM/YYYY", ephemeral=True)
            return

        roles = [role for role in [role1, role2, role3] if role is not None]

        embed = discord.Embed(title=f"Mở đăng kí tham gia sự kiện mới!", color=discord.Color.blue())
        embed.add_field(name="Sự kiện:", value=event_name, inline=False)
        embed.add_field(name="Thời gian tổ chức", value=event_datetime, inline=False)
        embed.add_field(name="Hạn chót đăng ký", value=due_datetime, inline=True)
        embed.add_field(name="Role tham gia", value=", ".join([role.mention for role in roles]), inline=False)
        embed.add_field(name="Tham gia", value="0", inline=True)
        embed.add_field(name="Vắng mặt", value="0", inline=True)
        embed.add_field(name="Danh sách đăng kí tham gia:", value="Đang cập nhật...", inline=False)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        query = """
        INSERT INTO events (event_name, event_datetime, due_datetime, message_id, channel_id, guild_id)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        event_id = db.fetch_one(query, (event_name, event_dt, due_dt, message.id, interaction.channel_id, interaction.guild_id))

        for role in roles:
            query = """
            INSERT INTO event_roles (event_id, role_id)
            VALUES (%s, %s)
            """
            db.execute_query(query, (event_id[0], role.id))

        embed.set_field_at(6, name="Danh sách đăng kí tham gia:", value=f"https://gdgoc.uong.beer/event/{event_id[0]}", inline=False)
        embed.set_footer(text=f"ID sự kiện: {event_id[0]}")
        
        await message.edit(embed=embed)

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        now = datetime.datetime.now()
        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)

        query_due = """
        SELECT e.id, e.event_name, e.due_datetime, e.guild_id
        FROM events e
        WHERE DATE(e.due_datetime) BETWEEN %s AND %s
        """
        due_events = db.fetch_all(query_due, (today, tomorrow))

        for event in due_events:
            due_time = event['due_datetime'].replace(tzinfo=None)
            time_diff = due_time - now
            if datetime.timedelta(0) <= time_diff <= datetime.timedelta(hours=1):
                await self.send_due_reminder(event)

        query_event = """
        SELECT e.id, e.event_name, e.event_datetime, e.guild_id
        FROM events e
        WHERE DATE(e.event_datetime) BETWEEN %s AND %s
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

        query = """
        SELECT DISTINCT role_id FROM event_roles WHERE event_id = %s
        """
        role_records = db.fetch_all(query, (event['id'],))
        
        for role_record in role_records:
            role = guild.get_role(role_record['role_id'])
            if not role:
                continue

            query_reminded = """
            SELECT user_id FROM reminders 
            WHERE event_id = %s AND reminder_type = 'due'
            """
            reminded_users = set(user['user_id'] for user in db.fetch_all(query_reminded, (event['id'],)))

            query_registered = """
            SELECT user_id FROM participants WHERE event_id = %s
            """
            registered_users = set(user['user_id'] for user in db.fetch_all(query_registered, (event['id'],)))

            users_to_remind = [member for member in role.members 
                             if member.id not in reminded_users and member.id not in registered_users]

            for user in users_to_remind:
                try:
                    await user.send(
                        f"Lời nhắc: Bạn cần đăng ký tham gia sự kiện {event['event_name']} "
                        f"trước {event['due_datetime'].strftime('%H:%M %d/%m/%Y')}!"
                    )
                    
                    query = """
                    INSERT INTO reminders (event_id, user_id, reminder_type, sent_at)
                    VALUES (%s, %s, 'due', %s)
                    """
                    db.execute_query(query, (event['id'], user.id, datetime.datetime.now()))
                except:
                    pass

    async def send_event_reminder(self, event):
        guild = self.bot.get_guild(event['guild_id'])
        if not guild:
            return

        query = """
        SELECT p.user_id 
        FROM participants p
        LEFT JOIN reminders r ON p.user_id = r.user_id 
            AND r.event_id = %s AND r.reminder_type = 'event'
        WHERE p.event_id = %s AND p.status = 'going' AND r.user_id IS NULL
        """
        participants = db.fetch_all(query, (event['id'], event['id']))

        for participant in participants:
            try:
                user = await guild.fetch_member(participant['user_id'])
                if user:
                    await user.send(
                        f"Lời nhắc: Sự kiện {event['event_name']} sẽ diễn ra vào lúc "
                        f"{event['event_datetime'].strftime('%H:%M %d/%m/%Y')}, trong vòng 1 tiếng nữa. "
                        f"Hãy chuẩn bị kỹ càng cho sự kiện!"
                    )
                    query = """
                    INSERT INTO reminders (event_id, user_id, reminder_type, sent_at)
                    VALUES (%s, %s, 'event', %s)
                    """
                    db.execute_query(query, (event['id'], participant['user_id'], datetime.datetime.now()))
            except:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        query = """
        SELECT e.id, er.role_id 
        FROM events e 
        JOIN event_roles er ON e.id = er.event_id 
        WHERE e.message_id = %s
        """
        event_roles = db.fetch_all(query, (payload.message_id,))
        
        if event_roles:
            event_id = event_roles[0]['id']
            allowed_role_ids = [er['role_id'] for er in event_roles]
            
            guild = self.bot.get_guild(payload.guild_id)
            member = await guild.fetch_member(payload.user_id)
            
            if not any(role.id in allowed_role_ids for role in member.roles):
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
            try:
                message = await channel.fetch_message(message_id)
                embed = message.embeds[0]
                
                for i, field in enumerate(embed.fields):
                    if field.name == "Tham gia":
                        embed.set_field_at(i, name="Tham gia", value=str(going_count), inline=True)
                    elif field.name == "Vắng mặt":
                        embed.set_field_at(i, name="Vắng mặt", value=str(not_going_count), inline=True)
                
                await message.edit(embed=embed)
            except:
                pass

async def setup(bot):
    await bot.add_cog(EventHandler(bot))