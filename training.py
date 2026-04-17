import discord
from discord.ext import commands

# ===== CONFIG =====
POLICE_ROLE = 1405031312531918878
TRAINEE_ROLE = 1494623778439823422  # 🔥 ใส่ role ทดลองงาน
TRAINER_ROLE = 1405031312531918878  # 🔥 ใส่ role ผู้ฝึก
TRAINING_CHANNEL = 1494683271362248755  # 🔥 ห้อง ตร.ทดลองงาน
# ==================

trainee_data = {}


# ===== VIEW หลัก =====
class TrainingView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="🧑‍🏫 รับฝึกสอน", style=discord.ButtonStyle.primary)
    async def take(self, interaction: discord.Interaction, button):
        if TRAINER_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ เฉพาะผู้ฝึก", ephemeral=True)

        data = trainee_data[self.user_id]

        if data["trainer"]:
            return await interaction.response.send_message("❌ มีคนรับฝึกแล้ว", ephemeral=True)

        data["trainer"] = interaction.user.id
        data["status"] = "training"

        await interaction.message.reply(f"🧑‍🏫 ผู้ฝึก: {interaction.user.mention}")
        await interaction.response.send_message("✅ คุณรับฝึกแล้ว", ephemeral=True)

    @discord.ui.button(label="✅ ผ่าน", style=discord.ButtonStyle.success)
    async def pass_btn(self, interaction: discord.Interaction, button):
        data = trainee_data[self.user_id]

        if interaction.user.id != data["trainer"]:
            return await interaction.response.send_message("❌ ไม่ใช่ผู้ฝึก", ephemeral=True)

        data["status"] = "pass"

        await interaction.message.reply(
            "🎖️ ผ่านการฝึกแล้ว กดรับยศด้านล่าง",
            view=PassView(self.user_id)
        )

    @discord.ui.button(label="❌ ไม่ผ่าน", style=discord.ButtonStyle.danger)
    async def fail_btn(self, interaction: discord.Interaction, button):
        data = trainee_data[self.user_id]

        if interaction.user.id != data["trainer"]:
            return await interaction.response.send_message("❌ ไม่ใช่ผู้ฝึก", ephemeral=True)

        await interaction.response.send_modal(FailModal(self.user_id))


# ===== FAIL MODAL =====
class FailModal(discord.ui.Modal, title="ไม่ผ่านการฝึก"):
    reason = discord.ui.TextInput(label="เหตุผล", style=discord.TextStyle.paragraph)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        data = trainee_data[self.user_id]
        data["status"] = "fail"
        data["attempt"] += 1

        await interaction.response.send_message(
            f"❌ ไม่ผ่าน\nเหตุผล: {self.reason.value}\n🔁 สามารถแก้ตัวได้",
            view=RetryView(self.user_id)
        )


# ===== RETRY =====
class RetryView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="🔁 แก้ตัว", style=discord.ButtonStyle.secondary)
    async def retry(self, interaction: discord.Interaction, button):
        trainee_data[self.user_id]["status"] = "training"
        await interaction.response.send_message("🔁 เริ่มประเมินใหม่", ephemeral=True)


# ===== PASS VIEW =====
class PassView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="🎖️ รับยศ", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ ไม่ใช่คุณ", ephemeral=True)

        await interaction.response.send_message(
            "📄 กรุณาอ่านสัญญา",
            view=ContractView(),
            ephemeral=True
        )


# ===== CONTRACT =====
class ContractView(discord.ui.View):
    @discord.ui.button(label="✅ ตกลง", style=discord.ButtonStyle.success)
    async def agree(self, interaction: discord.Interaction, button):
        guild = interaction.guild
        member = interaction.user

        await member.add_roles(
            guild.get_role(POLICE_ROLE)
        )

        # ลบ role ทดลองงาน
        trainee_role = guild.get_role(TRAINEE_ROLE)
        if trainee_role:
            await member.remove_roles(trainee_role)

        await interaction.response.send_message("🎉 คุณได้รับยศแล้ว", ephemeral=True)

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button):
        await interaction.response.send_message("❌ ยกเลิก", ephemeral=True)


# ===== COG =====
class TrainingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def send_to_training(self, member, name, phone, invigilator):
        trainee_data[member.id] = {
            "trainer": None,
            "status": "waiting",
            "attempt": 1
        }

        channel = self.bot.get_channel(TRAINING_CHANNEL)

        embed = discord.Embed(title="📋 ผู้สมัครทดลองงาน", color=0x00ff00)
        embed.add_field(name="👤 ชื่อ", value=name)
        embed.add_field(name="📞 เบอร์", value=phone or "-", inline=False)
        embed.add_field(name="🧑‍🏫 ผู้คุมสอบ", value=invigilator, inline=False)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        self.bot.loop.create_task(
            channel.send(embed=embed, view=TrainingView(member.id))
        )


# ===== setup =====
async def setup(bot: commands.Bot):
    await bot.add_cog(TrainingCog(bot))