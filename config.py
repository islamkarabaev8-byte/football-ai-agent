import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHAT_ID = int(os.getenv("CHAT_ID", "0")) or None

# Время отправки: 22:00 по Алматы (UTC+5) = 17:00 UTC
REPORT_HOUR_UTC = 17
REPORT_MINUTE_UTC = 0
