import discord
from discord.ext import commands
from discord import ui, Interaction, SelectOption
import logging
import datetime

LEAVE_PANEL_CHANNEL_ID = 1405090095840886868 # ห้องเก็บปุ่ม "แจ้งลา"
LEAVE_CHANNEL_ID = 1406501084565864488  # ห้องส่งข้อมูลการลา

# ---------------- Modal ----------------
class LeaveForm(ui.Modal, title="แบบฟอร์มแจ้งลา"):
    leave_type = ui.TextInput(
        label="ประเภทการลา",
        placeholder="ตัวอย่าง: ลาป่วย, ลาธุระส่วนตัว (OC), ลาพักร้อน"
    )
    date_from = ui.TextInput(label="ตั้งแต่ (dd/mm/yyyy)", placeholder="01/01/2025")
    date_to = ui.TextInput(label="ถึง (dd/mm/yyyy)", placeholder="02/01/2025")
    reason = ui.TextInput(label="หมายเหตุ", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: Interaction):
        try:
            name = interaction.user.display_name.replace("[WPD] ", "")
            leave_type = self.leave_type.value
            start_date = self.date_from.value
            end_date = self.date_to.value
            note = self.reason.value if self.reason.value else "-"

            # บันทึกลง Google Sheet
            sheet = getattr(interaction.client, "leaveofabsence", None)
            if sheet:
                last_row = len(sheet.col_values(1))
                if last_row < 2:
                    last_row = 3
                else:
                    last_row += 1

                sheet.update(
                    values=[[name, leave_type, start_date, end_date, note]],
                    range_name=f"A{last_row}:E{last_row}"
                )

            else:
                logging.error("❌ leaveofabsence worksheet not found")

            # ส่ง Embed แจ้งการลา
            channel = await interaction.client.fetch_channel(LEAVE_CHANNEL_ID)
            embed = discord.Embed(
                title="📢 แจ้งการลา",
                color=discord.Color.blue()
            )
            embed.add_field(name="ชื่อ", value=name, inline=True)
            embed.add_field(name="ประเภทการลา", value=leave_type, inline=True)
            embed.add_field(name="วันที่ลา", value=f"{start_date} - {end_date}", inline=False)
            embed.add_field(name="หมายเหตุ", value=note, inline=False)

            await channel.send(embed=embed)
            await interaction.response.send_message("✅ ส่งคำขอลาสำเร็จแล้ว!", ephemeral=True)

        except Exception as e:
            logging.error(f"❌ Error in leave form: {e}")
            await interaction.response.send_message("❌ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง", ephemeral=True)

# ---------------- Button ----------------
class LeaveButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="แจ้งลา", style=discord.ButtonStyle.primary, custom_id="leave_button")
    async def leave_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(LeaveForm())

# ---------------- Cog ----------------
class AbsenceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.bot.leaveofabsence = self.bot.workbook.worksheet("leaveofabsence")
        except Exception as e:
            logging.error(f"❌ Cannot load worksheet 'leaveofabsence': {e}")
            self.bot.leaveofabsence = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ AbsenceCog loaded")
        self.bot.add_view(LeaveButton())  # ปุ่มถาวร

        channel = self.bot.get_channel(LEAVE_PANEL_CHANNEL_ID)
        if not channel:
            logging.error("❌ Cannot fetch leave panel channel")
            return

        # ป้องกันส่งซ้ำ
        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.components:
                return

        await channel.send("กดปุ่มด้านล่างเพื่อแจ้งการลา 👇", view=LeaveButton())

# ---------------- Setup ----------------
async def setup(bot: commands.Bot):
    await bot.add_cog(AbsenceCog(bot))
