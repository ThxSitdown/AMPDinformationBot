import discord
from discord.ext import commands
import logging
from datetime import datetime

# ===== CONFIG =====
HISTORY_CHANNEL_ID = 1405020047021183102

class History(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invites = {}  # guild_id: [invite list]

    @commands.Cog.listener()
    async def on_ready(self):
        # โหลด invite cache ตอนบอทออนไลน์
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except discord.Forbidden:
                logging.warning(f"⚠️ บอทไม่มีสิทธิ์ดู invite ของ {guild.name}")
        logging.info("📥 Invite cache loaded.")

    # อัปเดต invite cache เมื่อสร้าง invite ใหม่
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        guild_id = invite.guild.id
        self.invites[guild_id] = await invite.guild.invites()
        logging.info(f"📥 Invite created in {invite.guild.name}: {invite.code}")

    # อัปเดต invite cache เมื่อ invite ถูกลบ
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        guild_id = invite.guild.id
        self.invites[guild_id] = await invite.guild.invites()
        logging.info(f"📤 Invite deleted in {invite.guild.name}: {invite.code}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        inviter = None
        guild_id = member.guild.id
        invites_before = self.invites.get(guild_id, [])
        try:
            invites_after = await member.guild.invites()
        except discord.Forbidden:
            invites_after = []

        # ตรวจสอบ invite ที่มีการใช้เพิ่มขึ้น
        for new_invite in invites_after:
            for old_invite in invites_before:
                if new_invite.code == old_invite.code and new_invite.uses > old_invite.uses:
                    inviter = new_invite.inviter
                    break
            if inviter:
                break

        # อัปเดต invite cache
        self.invites[guild_id] = invites_after

        # ส่ง embed เข้า channel
        channel = member.guild.get_channel(HISTORY_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="สมาชิกเข้าร่วม",
                description=f"👋 ยินดีต้อนรับ {member.mention} เข้าสู่เซิร์ฟเวอร์!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="ชื่อผู้ใช้", value=f"{member} ({member.display_name})", inline=False)
            embed.add_field(name="User ID", value=member.id, inline=False)
            embed.add_field(name="เข้าร่วมเมื่อ", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
            if inviter:
                embed.add_field(name="เชิญโดย", value=f"{inviter.mention} ({inviter})", inline=False)
                logging.info(f"✅ {member} เข้ามาโดย {inviter}")
            else:
                embed.add_field(name="เชิญโดย", value="ไม่ทราบว่าใครเชิญ", inline=False)
                logging.info(f"✅ {member} เข้ามา (ไม่ทราบว่าใครเชิญ)")

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = member.guild.get_channel(HISTORY_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="สมาชิกออก",
                description=f"❌ {member.mention} ได้ออกจากเซิร์ฟเวอร์",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="ชื่อผู้ใช้", value=f"{member} ({member.display_name})", inline=False)
            embed.add_field(name="User ID", value=member.id, inline=False)

            logging.info(f"❌ {member} ออกจากเซิร์ฟเวอร์")
            await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(History(bot))
