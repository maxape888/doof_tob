import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Читаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка пути к базе данных
# Если в .env написано app/data/kbju.db, мы сделаем этот путь абсолютным
BASE_DIR = Path(__file__).resolve().parent
DB_PATH_RAW = os.getenv("DB_PATH", "data/kbju.db")
DB_PATH = BASE_DIR / DB_PATH_RAW

# Автоматически создаем папку для базы, если её нет
DB_PATH.parent.mkdir(parents=True, exist_ok=True)