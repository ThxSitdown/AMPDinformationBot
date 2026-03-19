import discord
from discord.ext import commands

class WipeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="delete_all_channels")
    @commands.has_permissions(administrator=True)
    async def delete_all_channels(self, ctx):
        """ลบทุกห้อง (text/voice/category) ในเซิร์ฟเวอร์"""
        guild = ctx.guild
        await ctx.send("⚠️ กำลังลบทุกห้อง... โปรดรอสักครู่")

        for channel in guild.channels:
            try:
                await channel.delete()
            except Exception as e:
                await ctx.send(f"❌ ลบ {channel.name} ไม่ได้: {e}")

        await ctx.send("✅ ลบทุกห้องเรียบร้อยแล้ว")

async def setup(bot: commands.Bot):
    await bot.add_cog(WipeCog(bot))
