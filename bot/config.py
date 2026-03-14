import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "bot.db"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
EXCEL_SERVICES_PATH = os.getenv("EXCEL_SERVICES_PATH", str(BASE_DIR / "services.xlsx"))

# YCLIENTS настройки (можно заполнить через переменные окружения)
YCLIENTS_BASE_URL = os.getenv("YCLIENTS_BASE_URL", "https://api.yclients.com")
YCLIENTS_TOKEN = os.getenv("YCLIENTS_TOKEN", "")
YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID", "")

# Telegram ID специалистов (заполните реальными значениями)
SPECIALISTS = {
    "Марина": int(os.getenv("SPECIALIST_MARINA_ID", "0")),
    "Елизавета": int(os.getenv("SPECIALIST_ELIZAVETA_ID", "0")),
    "Ирина": int(os.getenv("SPECIALIST_IRINA_ID", "0")),
    "Татьяна": int(os.getenv("SPECIALIST_TATYANA_ID", "0")),
}
