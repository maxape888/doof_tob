import sqlite3
from config import DB_PATH

def fill_data():
    # Список продуктов: Название, Калории, Белки, Жиры, Углеводы
    foods = [
        ('Курица', 165.0, 31.0, 3.6, 0.0),
        ('Куриное филе', 110.0, 23.0, 1.0, 0.0),
        ('Рис', 130.0, 2.7, 0.3, 28.0),
        ('Яйцо', 155.0, 13.0, 11.0, 1.1)
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Очистим старое (опционально) и зальем новое
    cur.executemany(
        "INSERT OR IGNORE INTO foods (name, kcal, protein, fat, carbs) VALUES (?, ?, ?, ?, ?)", 
        foods
    )
    
    conn.commit()
    conn.close()
    print(f"✅ Продукты добавлены в {DB_PATH}")

if __name__ == "__main__":
    fill_data()