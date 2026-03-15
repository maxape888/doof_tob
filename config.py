import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Читаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка пути к базе данных
# Если в .env написано app/data/kbju.db, мы сделаем этот путь абсолютным
BASE_DIR = Path(__file__).resolve().parent.parent 

# Берем путь из .env (там должно быть просто data/calories_v2.db)
DB_PATH_RAW = os.getenv("DB_PATH", "data/calories_v2.db")

# Теперь это будет точно /app/data/calories_v2.db
DB_PATH = BASE_DIR / DB_PATH_RAW

# Создаем папку, если её нет
DB_PATH.parent.mkdir(parents=True, exist_ok=True)