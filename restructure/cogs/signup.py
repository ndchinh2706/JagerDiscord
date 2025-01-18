import discord
from discord.ext import commands
from discord import app_commands
from utils.database import db

class Signup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.signup_sessions = {}

    @app_commands.command(name="signup", description="Đăng ký hoặc cập nhật thông tin người dùng")
    async def signup(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        # Kiểm tra xem người dùng đã đăng ký chưa
        query = "SELECT * FROM users WHERE user_id = %s"
        user_data = db.fetch_one(query, (user_id,))
        
        if user_data:
            # Người dùng đã đăng ký
            view = EditConfirmView(self)
            await interaction.response.send_message(
                "Bạn đã đăng ký trước đó. Bạn có muốn chỉnh sửa thông tin cá nhân không?",
                view=view,
                ephemeral=True
            )
        else:
            # Người dùng chưa đăng ký
            await interaction.response.send_message("Bot đã gửi tin nhắn riêng cho bạn để bắt đầu quá trình đăng ký.", ephemeral=True)
            await self.start_signup(interaction.user)

    async def start_signup(self, user):
        dm_channel = await user.create_dm()
        await dm_channel.send("Vui lòng nhập đầy đủ họ và tên:")
        self.signup_sessions[user.id] = {"step": "fullname"}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        user_id = message.author.id
        if user_id not in self.signup_sessions:
            return

        session = self.signup_sessions[user_id]

        if session["step"] == "fullname":
            fullname = message.content
            session["fullname"] = fullname
            session["step"] = "student_id"
            await message.channel.send("Vui lòng nhập mã sinh viên:")
        elif session["step"] == "student_id":
            student_id = message.content
            if not self.validate_student_id(student_id):
                await message.channel.send("Mã sinh viên không hợp lệ. Vui lòng nhập lại mã sinh viên:")
                return
            session["student_id"] = student_id
            
            # Lưu thông tin vào cơ sở dữ liệu
            self.save_user_info(user_id, session["fullname"], session["student_id"])
            
            await message.channel.send("Đăng ký thành công! Cảm ơn bạn đã cung cấp thông tin.")
            del self.signup_sessions[user_id]


    def validate_student_id(self, student_id):
        return student_id.isalnum() and len(student_id) >= 5

    def save_user_info(self, user_id, fullname, student_id):
        query = """
        INSERT INTO users (user_id, fullname, student_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET fullname = EXCLUDED.fullname, student_id = EXCLUDED.student_id
        """
        db.execute_query(query, (user_id, fullname, student_id))

class EditConfirmView(discord.ui.View):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    @discord.ui.button(label="Chỉnh sửa", style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Bot đã gửi tin nhắn riêng cho bạn để bắt đầu quá trình chỉnh sửa thông tin.", ephemeral=True)
        await self.cog.start_signup(interaction.user)

async def setup(bot):
    await bot.add_cog(Signup(bot))