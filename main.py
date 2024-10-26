import constants
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import datetime
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    GUILD_ID = constants.Discord_GUILD_ID
    guild = discord.Object(id=GUILD_ID)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f'Đã đồng bộ {len(synced)} lệnh cho máy chủ {GUILD_ID}')
    except Exception as e:
        print(e)
    print(f'Đăng nhập thành công: {bot.user}')

@bot.tree.command(name='event', description='Tạo một sự kiện để các thành viên xác nhận tham gia')
@app_commands.describe(event_name='Tên sự kiện', event_date='Ngày tổ chức sự kiện', role='Vai trò tham gia sự kiện', due_date="Hạn đăng kí tham gia")
async def create_event(interaction: discord.Interaction, event_name: str, event_date: str, role: discord.Role, due_date: str):
    attend_button = Button(label='Có mặt', style=discord.ButtonStyle.success)
    decline_button = Button(label='Vắng mặt', style=discord.ButtonStyle.danger)

    try:
        event_date_obj = datetime.strptime(event_date, "%d/%m/%Y") #tạm để đó bữa nào làm được cái DM thì làm lun hehe
        due_date_obj = datetime.strptime(due_date, "%d/%m/%Y")
    except ValueError:
        await interaction.response.send_message("Ngày không hợp lệ! Vui lòng sử dụng định dạng DD/MM/YYYY.", ephemeral=True)
        return
    if due_date_obj >= event_date_obj:
        await interaction.response.send_message("Hạn đăng kí phải trước ngày tổ chức sự kiện.", ephemeral=True)
        return
    
    attendees = []
    absentees = []
    not_voted = [member for member in role.members]  #Đếch hiểu sao không get được role.members.
    print(role.members)
    async def update_event_message(event_message):
        attending_count = len(attendees)
        not_attending_count = len(absentees)
        not_voted_count = len(not_voted) - attending_count - not_attending_count
        content = (
            f'Sự kiện: **{event_name}**\n'
            f'Ngày tổ chức: {event_date}\n'
            f'Vai trò: {role.mention}\n\n'
            f'Hạn đăng ký tham gia: {due_date}\n\n'
            f'✅ Có mặt: {attending_count}\n'
            f'❌ Vắng mặt: {not_attending_count}\n'
            f'❓ Chưa bình chọn: {not_voted_count}'
        )

        await event_message.edit(content=content, view=view)

    async def attend_callback(interaction_button: discord.Interaction):
        if (due_date_obj > d):
            if role in interaction_button.user.roles:
                if interaction_button.user not in attendees:
                    attendees.append(interaction_button.user)
                    if interaction_button.user in absentees:
                        absentees.remove(interaction_button.user)
                    if interaction_button.user in not_voted:
                        not_voted.remove(interaction_button.user)
                await interaction_button.response.send_message(f'{interaction_button.user.name} sẽ có mặt!', ephemeral=True)
                await update_event_message(event_message)
            else:
                await interaction_button.response.send_message('Bạn không có quyền tham gia sự kiện này.', ephemeral=True)
        else:
            await interaction_button.response.send_message('Đã hết thời gian đăng kí sự kiện.', ephemeral=True)

    async def decline_callback(interaction_button: discord.Interaction):
        if role in interaction_button.user.roles:
            if interaction_button.user not in absentees:
                absentees.append(interaction_button.user)
                if interaction_button.user in attendees:
                    attendees.remove(interaction_button.user)
                if interaction_button.user in not_voted:
                    not_voted.remove(interaction_button.user)
            await interaction_button.response.send_message(f'{interaction_button.user.name} sẽ vắng mặt.', ephemeral=True)
            await update_event_message(event_message)
        else:
            await interaction_button.response.send_message('Bạn không có quyền tham gia sự kiện này.', ephemeral=True)

    attend_button.callback = attend_callback
    decline_button.callback = decline_callback

    view = View()
    view.add_item(attend_button)
    view.add_item(decline_button)

    event_message = await interaction.channel.send(
        f'Sự kiện: **{event_name}**\nNgày tổ chức: {event_date}\nVai trò: {role.mention}\n\n✅ Có mặt: 0\n❌ Vắng mặt: 0\n❓ Chưa bình chọn: {len(not_voted)}',
        view=view
    )

bot.run(constants.Discord_API_KEY_bot)
