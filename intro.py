import discord
from discord.ext import commands

# ====== CONFIG ======
ROLE_ID = 1405482088660205568
ROLE_TRAINEE = 1313457513093533747
LOG_CHANNEL_ID = 1406877872098115674
WELCOME_CHANNEL_ID = 1408136216569708786
# =====================

class IntroModal(discord.ui.Modal, title="กรอกข้อมูลแนะนำตัว"):
    policeid = discord.ui.TextInput(label="รหัสประจำตัว", placeholder="ถามจากผู้คุมสอบ")
    name = discord.ui.TextInput(label="ชื่อ IC", placeholder="เช่น Sitdown Jubmuah")
    phone = discord.ui.TextInput(label="เบอร์ IC", placeholder="เช่น 01234", required=False)
    Steam = discord.ui.TextInput(label="SteamHex", required=False)
    invigilator = discord.ui.TextInput(label="ผู้คุมสอบ", placeholder="ชื่อของผู้ที่สอบคุณเข้ามา")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        #  เปลี่ยนชื่อเล่น (Nickname)
        new_nick = f"{self.policeid.value} [WPD] {self.name.value}"
        try:
            await member.edit(nick=new_nick, reason="ตั้งชื่อ IC ตอนแนะนำตัว")
        except discord.Forbidden:
            await interaction.response.send_message("❌ บอทไม่มีสิทธิ์เปลี่ยนชื่อคุณ", ephemeral=True)
            return

        #  เพิ่ม role
        roles_to_add = [guild.get_role(rid) for rid in (ROLE_ID, ROLE_TRAINEE) if guild.get_role(rid)]
        if roles_to_add:
            await member.add_roles(*roles_to_add, reason="ผ่านการแนะนำตัว")

        #  ส่ง log
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(title="สมาชิกใหม่", color=0x00ff00)
        embed.add_field(name="รหัสประจำตัว", value=self.policeid.value, inline=False)
        embed.add_field(name="ชื่อIC", value=self.name.value, inline=False)
        embed.add_field(name="เบอร์IC", value=self.phone.value or "-", inline=False)
        embed.add_field(name="SteamHex", value=self.Steam.value or "-", inline=False)
        embed.add_field(name="ผู้คุมสอบ", value=self.invigilator.value, inline=False)
        

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        embed.set_footer(text=f"User ID: {interaction.user.id}")
        await log_channel.send(embed=embed)

        await interaction.response.send_message("✅ เยี่ยม! ขอให้สนุกกับการทำงาน", ephemeral=True)


# ====== ปุ่ม ======
class IntroButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 กรอกข้อมูลและรับยศ", style=discord.ButtonStyle.primary, custom_id="intro_button")
    async def intro_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IntroModal())


# ====== Cog ======
class IntroCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ IntroCog loaded")
        self.bot.add_view(IntroButton())  # ✅ ปุ่มถาวร
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

        # ป้องกันส่งซ้ำ
        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.components:
                return

        await channel.send(
            "👋 ยินดีต้อนรับเจ้าหน้าที่ฝึกหัดคนใหม่! กดปุ่มด้านล่างเพื่อกรอกข้อมูล และรับยศ",
            view=IntroButton()
        )


# ====== setup ======
async def setup(bot: commands.Bot):
    await bot.add_cog(IntroCog(bot))
