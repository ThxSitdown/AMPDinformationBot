import discord
import gspread
import json
import re
import logging
import threading
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
from discord.ext import commands
import os
import time

# ================== CONFIG ==================
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
DUTY_CHANNEL_ID = 1408080182325153975

# Fallback local file
if not DISCORD_BOT_TOKEN:
    try:
        with open("discord_token.txt", "r", encoding="utf-8") as f:
            DISCORD_BOT_TOKEN = f.read().strip()
    except FileNotFoundError:
        logging.error("❌ Discord token file not found.")

if not GOOGLE_CREDENTIALS:
    try:
        with open("google_credentials.json", "r", encoding="utf-8") as f:
            GOOGLE_CREDENTIALS = f.read()
    except FileNotFoundError:
        logging.error("❌ Google credentials file not found.")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ================== DISCORD BOT ==================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.workbook = None
        self.sheet = None
        self.log_red_case = None
        self.log_black_case = None
        self.log_take2 = None

    async def setup_hook(self):
        # โหลด extensions รวมถึง wipe
        extensions = ["intro", "history", "absence", "case", "wipe"]
        for ext in extensions:
            try:
                await self.load_extension(ext)
                logging.info(f"✅ Loaded extension: {ext}")
            except Exception as e:
                logging.error(f"❌ Failed to load extension {ext}: {e}")

bot = MyBot()

# ================== FLASK ==================
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running."

@app.route('/health')
def health_check():
    return {"status": "ok", "bot_status": bot.is_ready()}

def run_flask():
    port = int(os.getenv("PORT", 5000))
    logging.info(f"🌍 Starting Flask on port {port}...")
    app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)

# ================== GOOGLE SHEETS ==================
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
sheet = None

if GOOGLE_CREDENTIALS:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDENTIALS), SCOPE)
        client = gspread.authorize(creds)
        workbook = client.open("DataWPD")
        bot.workbook = workbook

        # worksheets
        sheet = workbook.worksheet("Logduty")
        bot.sheet = sheet
        bot.log_red_case = workbook.worksheet("LogRedcase")
        bot.log_black_case = workbook.worksheet("Logcase")
        bot.log_take2 = workbook.worksheet("LogTake2")

        logging.info("✅ Google Sheets connected successfully.")
    except Exception as e:
        logging.error(f"❌ Google Sheets connection failed: {e}")

# ================== FUNCTIONS ==================
def format_datetime(raw_time):
    pattern = r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})"
    match = re.search(pattern, raw_time)
    if match:
        d, m, y, h, mi, s = match.groups()
        return f"{int(d):02d}/{int(m):02d}/{y} {int(h):02d}:{int(mi):02d}:{int(s):02d}"
    return raw_time

def save_to_sheet(sheet, values):
    try:
        last_row = len(sheet.col_values(1)) + 1
        sheet.update(values=[values], range_name=f"A{last_row}:C{last_row}")
        logging.info(f"✅ Saved to Google Sheets: {values}")
    except Exception as e:
        logging.error(f"❌ Cannot save to Google Sheets: {e}")

# ================== EVENTS ==================
@bot.event
async def on_ready():
    logging.info(f"🤖 {bot.user} is online and ready!")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        if message.channel.id == DUTY_CHANNEL_ID and message.author.name == "ออกเวรหน่วยงาน":
            name, check_in_time, check_out_time = None, None, None

            if message.embeds:
                for embed in message.embeds:
                    if embed.description:
                        desc = re.sub(r"\*\*", "", embed.description)

                        name_match = re.search(r"เจ้าหน้าที่\s+(.+?)\s+ได้ทำการออกเวร", desc)
                        if name_match:
                            name = name_match.group(1).strip()

                        in_match = re.search(r"เวลาเข้างาน\s*:\s*(\d{1,2}/\d{1,2}/\d{4}\s\d{1,2}:\d{2}:\d{2})", desc)
                        if in_match:
                            check_in_time = format_datetime(in_match.group(1))

                        out_match = re.search(r"เวลาออกงาน\s*:\s*(\d{1,2}/\d{1,2}/\d{4}\s\d{1,2}:\d{2}:\d{2})", desc)
                        if out_match:
                            check_out_time = format_datetime(out_match.group(1))

            if all([name, check_in_time, check_out_time]) and sheet:
                save_to_sheet(sheet, [name, check_in_time, check_out_time])
            else:
                logging.warning(f"⚠️ Missing data: {name}, {check_in_time}, {check_out_time}")

    await bot.process_commands(message)

# ================== RUN ==================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()

    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)

    while True:
        time.sleep(60)
