import sqlite3
import os
from config import DB_PATH # Используем тот же путь, что и в fresh_db.py

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- ПОИСК ПРОДУКТОВ (подстроено под kcal, protein, fat, carbs) ---

def search_foods(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Гибкий поиск по подстроке
    cursor.execute("""
        SELECT id, name, kcal, protein, fat, carbs FROM foods 
        WHERE LOWER(name) LIKE ? 
        ORDER BY LENGTH(name) ASC 
        LIMIT 10
    """, ('%' + query.lower() + '%',))
    results = cursor.fetchall()
    conn.close()
    return results

def get_food_by_id(food_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
    result = cursor.fetchone()
    conn.close()
    return result

# --- ПОЛЬЗОВАТЕЛИ ---

def upsert_user_profile(user_id, gender, age, height, weight, activity_text, daily_norm):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO users (user_id, age, weight, height, gender, activity, daily_norm)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, age, weight, height, gender, activity_text, daily_norm))
    conn.commit()
    conn.close()
    return daily_norm

def get_user_profile(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

# --- ЛОГИ (ПРИЕМЫ ПИЩИ) ---

def log_meal(user_id, kcal, p, f, c, details, meal_name="Прием пищи"):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO logs (user_id, kcal, protein, fat, carbs, details, meal_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, kcal, p, f, c, details, meal_name))
    conn.commit()
    conn.close()

def get_daily_logs(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT kcal, protein, fat, carbs, details, meal_name,
               strftime('%H:%M', timestamp) as meal_time
        FROM logs 
        WHERE user_id = ? AND date = date('now', 'localtime')
        ORDER BY timestamp ASC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_daily_stats(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    # Проверь, что здесь protein, fat, carbs (как в твоем fresh_db)
    cur.execute("""
        SELECT SUM(kcal) as total_kcal, 
               SUM(protein) as total_prot, 
               SUM(fat) as total_fat, 
               SUM(carbs) as total_carb
        FROM logs 
        WHERE user_id = ? AND date = date('now', 'localtime')
    """, (user_id,))
    stats = cur.fetchone()
    conn.close()
    return stats

def reset_user_data(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM logs WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True