import discord
from discord.ext import commands
import re
import logging

CASE_CHANNEL_ID = 1405512160582303786

class CaseCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logging.info("✅ CaseCog initialized") 

    # ฟังก์ชันบันทึกลง Google Sheets
    def save_to_sheet(self, sheet, values):
        try:
            last_row = len(sheet.col_values(1)) + 1
            sheet.update(values=[values], range_name=f"A{last_row}:B{last_row}")
            logging.info(f"✅ Saved to Google Sheets ({sheet.title}): {values}")
        except Exception as e:
            logging.error(f"❌ Cannot save to Google Sheets ({sheet.title}): {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot and message.webhook_id is None:
            return

        if message.channel.id != CASE_CHANNEL_ID:
            return

        officer_name, case_details = None, None
        target_sheet = None

        # ================= ตรวจสอบ Embed =================
        if message.embeds:
            embed = message.embeds[0]

            parts = []
            if embed.title:
                parts.append(embed.title)
            if embed.description:
                parts.append(embed.description)
            if embed.fields:
                for field in embed.fields:
                    parts.append(field.name)
                    parts.append(field.value)

            # รวมทั้งหมดเป็นข้อความเดียว
            description = " ".join(parts)

            # clean header
            description = re.sub(r"WISH CASE REPORTS SYSTEM", "", description, flags=re.IGNORECASE)
            description = re.sub(r"ระบบส่งเคสตำรวจ", "", description, flags=re.IGNORECASE)
            description = description.replace("**", "").strip()

            case_match = re.search(
                r"^(?P<officer>.+?)\s+ได้ทำรายการ\s+(?P<case>.+?)(?:\s+คุณ.*)?$",
                description.strip(),
                re.DOTALL | re.IGNORECASE
            )
            if case_match:
                officer_name = case_match.group("officer").strip()
                case_details = case_match.group("case").strip()

        # ================= เลือก worksheet =================
        if officer_name and case_details:
            if re.search(r"take\s*2", case_details, re.IGNORECASE) and hasattr(self.bot, "log_take2"):
                target_sheet = self.bot.log_take2
            elif re.search(r"\bred\b", case_details, re.IGNORECASE) and hasattr(self.bot, "log_red_case"):
                target_sheet = self.bot.log_red_case
            elif hasattr(self.bot, "log_black_case"):
                target_sheet = self.bot.log_black_case

            if target_sheet:
                self.save_to_sheet(target_sheet, [officer_name, case_details])
        else:
            logging.warning("⚠️ Case format not recognized")

        await self.bot.process_commands(message)

# SETUP
async def setup(bot: commands.Bot):
    await bot.add_cog(CaseCog(bot))
    logging.info("✅ CaseCog loaded")
