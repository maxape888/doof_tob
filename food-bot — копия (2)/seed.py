import sqlite3
import os
from config import DB_PATH

def setup_database():
    # Создаем папку для базы, если её нет (например, FOOD-BOT/data/)
    db_dir = DB_PATH.parent
    if not db_dir.exists():
        os.makedirs(db_dir)
        print(f"Создана папка: {db_dir}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Создаем таблицу ровно из 6 колонок (как ожидает ваш handlers.py)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            kcal REAL NOT NULL,
            protein REAL NOT NULL,
            fat REAL NOT NULL,
            carbs REAL NOT NULL
        )
    """)

    # Тестовые данные
    products = [
        ('банан', 89.0, 1.1, 0.3, 22.8),
        ('куриная грудка', 113.0, 23.6, 1.9, 0.4),
        ('гречка', 330.0, 12.6, 3.3, 62.1),
        ('яйцо', 155.0, 12.7, 11.5, 0.7)
    ]

    cur.executemany(
        "INSERT OR REPLACE INTO foods (name, kcal, protein, fat, carbs) VALUES (?, ?, ?, ?, ?)",
        products
    )

    conn.commit()
    conn.close()
    print(f"✅ Готово! Таблица создана в: {DB_PATH}")

if __name__ == "__main__":
    setup_database()