import discord
from discord.ext import commands


# ====== CONFIG ======
POLICE_ROLE = 1494623778439823422
DOCTOR_ROLE = 1479831488332828703 

LOG_CHANNEL_ID = 1405031839877300356
WELCOME_CHANNEL_ID = 1405034341133844501
# =====================


# ====== MODAL ตำรวจ ======
class PoliceModal(discord.ui.Modal, title="รายงานตัวตำรวจ"):
    name = discord.ui.TextInput(label="ชื่อ IC")
    phone = discord.ui.TextInput(label="เบอร์ IC", required=False)
    steam = discord.ui.TextInput(label="SteamHex", required=False)
    invigilator = discord.ui.TextInput(label="ผู้คุมสอบ")

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user
        guild = interaction.guild

        # เปลี่ยนชื่อ
        try:
            await member.edit(nick=f"[AMPD] {self.name.value}")
        except:
            pass

        # เพิ่ม role
        role = guild.get_role(POLICE_ROLE)
        if role:
            await member.add_roles(role)

        # embed log
        embed = discord.Embed(title="👮 รายงานตัวตำรวจ", color=0x1A00B8)
        embed.add_field(name="ชื่อ", value=self.name.value)
        embed.add_field(name="SteamHex", value=self.steam.value, inline=False)
        embed.add_field(name="เบอร์IC", value=self.phone.value, inline=False)
        embed.add_field(name="ผู้คุมสอบ", value=self.invigilator.value, inline=False)
        

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)


        await interaction.guild.get_channel(LOG_CHANNEL_ID).send(embed=embed)

        await interaction.response.send_message("✅ รับยศตำรวจเรียบร้อย", ephemeral=True)

        training_cog = interaction.client.get_cog("TrainingCog")

        if training_cog:
            training_cog.send_to_training(
                member,
                self.name.value,
                self.phone.value,
                self.invigilator.value
            )


# ====== MODAL หมอ ======
class DoctorModal(discord.ui.Modal, title="รายงานตัวแพทย์"):
    name = discord.ui.TextInput(label="ชื่อ IC")
    phone = discord.ui.TextInput(label="เบอร์ IC", required=False)
    steamMD = discord.ui.TextInput(label="SteamHex", required=False)
    invigilatorMD = discord.ui.TextInput(label="ผู้คุมสอบ")

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user
        guild = interaction.guild

        # เปลี่ยนชื่อ (หมอ)
        try:
            await member.edit(nick=f"[AMMD] {self.name.value}")
        except:
            pass

        # เพิ่ม role หมอ
        role = guild.get_role(DOCTOR_ROLE)
        if role:
            await member.add_roles(role)

        # embed log
        embed = discord.Embed(title="🩺 รายงานตัวแพทย์", color=0xFFFFFF)
        embed.add_field(name="ชื่อ", value=self.name.value)
        embed.add_field(name="SteamHex", value=self.steamMD.value, inline=False)
        embed.add_field(name="เบอร์IC", value=self.phone.value, inline=False)
        embed.add_field(name="ผู้คุมสอบ", value=self.invigilatorMD.value, inline=False)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        await interaction.guild.get_channel(LOG_CHANNEL_ID).send(embed=embed)

        await interaction.response.send_message("✅ รับยศหมอเรียบร้อย", ephemeral=True)


# ====== VIEW ปุ่ม ======
class SelectRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👮‍♂️ ตำรวจ", style=discord.ButtonStyle.primary, custom_id="police_btn")
    async def police(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PoliceModal())

    @discord.ui.button(label="🩺 หมอ", style=discord.ButtonStyle.success, custom_id="doctor_btn")
    async def doctor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DoctorModal())


# ====== COG ======
class IntroCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Role Select Loaded")

        self.bot.add_view(SelectRoleView())

        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

        # กันส่งซ้ำ
        async for msg in channel.history(limit=10):
            if msg.author == self.bot.user and msg.components:
                return

        embed = discord.Embed(
            title="👋 ระบบรายงานตัว",
            description="กรุณาเลือกหน่วยงาน",
            color=discord.Color.gold()
        )

        embed.set_image(url="https://cdn.discordapp.com/attachments/1474376876217860241/1490229758045327411/Agency1000x1000.gif?ex=69d34c1d&is=69d1fa9d&hm=d224e7d7ec6d0c3a5255576a91b76c1510bd1cfcfacde92dfd21f302ac327a44&")

        await channel.send(embed=embed, view=SelectRoleView())


# ====== setup ======
async def setup(bot: commands.Bot):
    await bot.add_cog(IntroCog(bot))