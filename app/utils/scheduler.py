from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from ..utils.database import get_db_connection

async def send_reminders(bot: Bot):
    # Получаем список всех пользователей из базы
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    conn.close()

    for user in users:
        try:
            user_id = user['user_id']
            # Здесь можно добавить проверку: если пользователь сегодня уже ел, не писать ему
            await bot.send_message(
                user_id, 
                "🔔 <b>Напоминание</b>\nНе забудьте записать ваш последний прием пищи, чтобы статистика была точной! 🍎",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Не удалось отправить напоминание {user['user_id']}: {e}")

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow") # Укажи свой часовой пояс
    
    # Напоминания в 14:00 (обед) и 20:00 (ужин)
    scheduler.add_job(send_reminders, 'cron', hour=11, minute=30, args=[bot])
    scheduler.add_job(send_reminders, 'cron', hour=19, minute=46, args=[bot])
    
    return scheduler