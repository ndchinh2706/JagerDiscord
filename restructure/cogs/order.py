import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.transaction import total_amount_for_ticket
import asyncio
import aiofiles
import urllib.parse

class OrderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_tasks = {}
        self.close_locks = {}
        self.bot.loop.create_task(self.restore_open_tickets())

    @app_commands.command(name="order", description="Tạo một order mới")
    async def order(self, interaction: discord.Interaction):
        view = discord.ui.View()
        button = discord.ui.Button(label="Tạo order", style=discord.ButtonStyle.primary)
        
        async def button_callback(button_interaction):
            await self.create_ticket(button_interaction)

        button.callback = button_callback
        view.add_item(button)
        
        await interaction.response.send_message("Nhấn nút dưới đây để tạo order:", view=view, ephemeral=True)

    async def create_ticket(self, interaction):
        try:
            query = "SELECT nextval('ticket_id_seq')"
            result = db.fetch_one(query)
            sequence_value = result['nextval']

            ticket_id = f"TICKET{sequence_value}GDGOC"

            query = "INSERT INTO tickets (ticket_id, user_id) VALUES (%s, %s) RETURNING id"
            result = db.fetch_one(query, (ticket_id, interaction.user.id))
            
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name="Order Tickets")
            if not category:
                category = await guild.create_category("Order Tickets")

            channel_name = f"order-{ticket_id}"
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            order_role = discord.utils.get(guild.roles, name="Order")
            if order_role:
                overwrites[order_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

            db.execute_query("UPDATE tickets SET channel_id = %s WHERE ticket_id = %s", (channel.id, ticket_id))

            await self.send_ticket_message(channel, ticket_id, 0)

            task = asyncio.create_task(self.update_payment_info(channel, ticket_id))
            self.update_tasks[ticket_id] = task

            await interaction.response.send_message(f"Đã tạo order ticket {ticket_id}. Vui lòng kiểm tra kênh {channel.mention}", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("Có lỗi xảy ra khi tạo order. Vui lòng thử lại sau.", ephemeral=True)

    async def update_payment_info(self, channel, ticket_id):
        try:
            while True:
                if channel.guild is None or channel not in channel.guild.channels:
                    db.execute_query("UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE ticket_id = %s", (ticket_id,))
                    break

                new_total_amount = total_amount_for_ticket(ticket_id)
                result = db.fetch_one("SELECT amount FROM tickets WHERE ticket_id = %s", (ticket_id,))
                
                if result and result['amount'] != new_total_amount:
                    await channel.purge(check=lambda m: m.author == self.bot.user)
                    await self.send_ticket_message(channel, ticket_id, new_total_amount)
                    db.execute_query("UPDATE tickets SET amount = %s WHERE ticket_id = %s", (new_total_amount, ticket_id))

                await asyncio.sleep(5)

        except Exception as e:
            pass
        finally:
            self.update_tasks.pop(ticket_id, None)

    async def send_ticket_message(self, channel, ticket_id, amount):
        image_url = f"https://api.vietqr.io/image/970422-066060606-xsU52l1.jpg?accountName=NGUYEN%20DINH%20CHINH&amount=0&addInfo={urllib.parse.quote(ticket_id)}"
        
        embed = discord.Embed(title=f"Order Ticket: {ticket_id}", 
                              description="Chào mừng đến với order của bạn! Hãy gủi vào đây order của bạn. LƯU Ý: CHỈ ĐÓNG ORDER KHI ĐÃ NHẬN ĐƯỢC ĐẦY ĐỦ ORDER!", 
                              color=discord.Color.blue())
        embed.set_image(url=image_url)
        embed.add_field(name="Hướng dẫn", value="Vui lòng chuyển khoản vào QR dưới đây và đợi xác nhận.")
        embed.add_field(name="Số tiền thanh toán đã nhận:", value=f"{amount:,.0f} VND", inline=False)
        embed.set_footer(text="Cảm ơn bạn đã quẹt quẹt cái QR hihi!")

        close_button = discord.ui.Button(label="Đóng Order", style=discord.ButtonStyle.danger, custom_id=f"close_{ticket_id}")
        
        async def close_callback(interaction: discord.Interaction):
            user_id = db.fetch_one("SELECT user_id FROM tickets WHERE ticket_id = %s", (ticket_id,))['user_id']
            if interaction.user.id == user_id or discord.utils.get(interaction.user.roles, name="Order"):
                await self.confirm_close_ticket(interaction, interaction.channel, ticket_id)

        close_button.callback = close_callback
        view = discord.ui.View()
        view.add_item(close_button)

        await channel.send(embed=embed, view=view)

    async def confirm_close_ticket(self, interaction, channel, ticket_id):
        confirm_view = discord.ui.View()
        confirm_button = discord.ui.Button(label="Xác nhận đóng", style=discord.ButtonStyle.danger)
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        async def confirm_callback(confirm_interaction):
            if confirm_interaction.user.id == interaction.user.id:
                await self.close_ticket(confirm_interaction, channel, ticket_id)

        async def cancel_callback(cancel_interaction):
            if cancel_interaction.user.id == interaction.user.id:
                await cancel_interaction.response.send_message("Đã hủy việc đóng order.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        confirm_view.add_item(confirm_button)
        confirm_view.add_item(cancel_button)

        await interaction.response.send_message("Bạn có chắc chắn muốn đóng order này không?", view=confirm_view, ephemeral=True)

    async def close_ticket(self, interaction, channel, ticket_id):
        if ticket_id not in self.close_locks:
            self.close_locks[ticket_id] = asyncio.Lock()

        async with self.close_locks[ticket_id]:
            await interaction.response.defer(ephemeral=True)

            update_task = self.update_tasks.pop(ticket_id, None)
            if update_task:
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass

            result = db.fetch_one("SELECT amount FROM tickets WHERE ticket_id = %s", (ticket_id,))
            final_amount = result['amount'] if result else 0

            db.execute_query("UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE ticket_id = %s", (ticket_id,))

            try:
                async with aiofiles.open('order.log', mode='a') as f:
                    await f.write(f"Order {ticket_id} đã đóng. Final amount: {final_amount:,.0f} VND\n")
                    async for message in channel.history(limit=None, oldest_first=True):
                        await f.write(f"{message.created_at} - {message.author}: {message.content}\n")

                await channel.send(f"Order đang được đóng. Tổng thanh toán cuối cùng: {final_amount:,.0f} VND")
                await asyncio.sleep(5)
                await channel.delete()
                
                await interaction.followup.send(f"Order {ticket_id} đã được đóng và kênh đã bị xóa.", ephemeral=True)
            except Exception as e:
                pass
        self.close_locks.pop(ticket_id, None)

    async def restore_open_tickets(self):
        await self.bot.wait_until_ready()
        query = "SELECT ticket_id, channel_id, user_id, amount FROM tickets WHERE status = 'open'"
        open_tickets = db.fetch_all(query)
        
        for ticket in open_tickets:
            ticket_id = ticket['ticket_id']
            channel_id = ticket['channel_id']
            channel = self.bot.get_channel(channel_id)
            
            if channel:
                await channel.purge(check=lambda m: m.author == self.bot.user)
                await self.send_ticket_message(channel, ticket_id, ticket['amount'])
                
                task = asyncio.create_task(self.update_payment_info(channel, ticket_id))
                self.update_tasks[ticket_id] = task
            else:
                db.execute_query("UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE ticket_id = %s", (ticket_id,))

async def setup(bot):
    await bot.add_cog(OrderCog(bot))