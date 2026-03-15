import sqlite3
import os
from config import DB_PATH  # Он возьмет путь из твоего конфига

def rebuild():
    # Если старый файл базы мешает, мы его удаляем
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑 Старая база {DB_PATH} удалена.")

    # Создаем новое подключение (это автоматически создаст файл .db)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("🛠 Создаем таблицы...")
    
    # Таблица пользователей
    cur.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        age INTEGER, weight REAL, height REAL, 
        gender TEXT, activity REAL, daily_norm REAL
    )""")

    # Таблица логов (здесь все те колонки, на которые ругался бот)
    cur.execute("""
    CREATE TABLE logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        kcal REAL, protein REAL, fat REAL, carbs REAL,
        details TEXT,
        meal_name TEXT,
        timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
        date DATE DEFAULT (date('now', 'localtime'))
    )""")

    # Таблица продуктов
    cur.execute("""
    CREATE TABLE foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        kcal REAL, protein REAL, fat REAL, carbs REAL
    )""")
    
    # Добавим яблоко, чтобы база не была совсем пустой
    cur.execute("INSERT INTO foods (name, kcal, protein, fat, carbs) VALUES (?, ?, ?, ?, ?)", 
                ("яблоко", 52, 0.3, 0.2, 14))

    conn.commit()
    conn.close()
    print(f"✅ Готово! Файл {DB_PATH} создан и настроен.")

if __name__ == "__main__":
    rebuild()