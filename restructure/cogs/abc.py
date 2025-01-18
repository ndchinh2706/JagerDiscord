# cogs/general.py
import discord
from discord.ext import commands
from utils.database import db

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def userinfo(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        query = "SELECT * FROM users WHERE user_id = %s"
        user_data = db.fetch_one(query, (user.id,))
        
        if user_data:
            # Process and send user data
            await ctx.send(f"User data: {user_data}")
        else:
            await ctx.send("User not found in the database.")

async def setup(bot):
    await bot.add_cog(General(bot))