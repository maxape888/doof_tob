import sys
import os
import asyncio
import logging

# Исправляем пути импорта
sys.path.append(os.path.join(os.getcwd()))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

# Импортируем твои модули
from app.handlers import register_handlers
from app.utils.scheduler import setup_scheduler
# Импортируем функцию инициализации базы данных
from app.utils.database import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# Загрузка токена из переменных окружения (Railway/Render) или из config.py
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    try:
        from config import BOT_TOKEN as LOCAL_TOKEN
        BOT_TOKEN = LOCAL_TOKEN
    except ImportError:
        pass

if not BOT_TOKEN:
    logging.error("КРИТИЧЕСКАЯ ОШИБКА: Токен бота (BOT_TOKEN) не найден!")
    sys.exit(1)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота / Проверить норму"),
        BotCommand(command="reset", description="Сбросить все данные и анкету"),
    ]
    await bot.set_my_commands(commands)

async def main():
    # 1. Инициализируем базу данных (создаем таблицы, если их нет)
    # Это исправит ошибку "no such table: logs"
    try:
        init_db()
        logging.info("База данных успешно инициализирована (таблицы проверены).")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        # Не выходим, пробуем запуститься дальше

    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация хендлеров
    register_handlers(dp)

    # Установка команд в меню
    await set_commands(bot)

    # Запуск планировщика
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logging.info("Планировщик напоминаний запущен!")

    logging.info("Бот успешно запущен и готов к работе!")

    try:
        # Сбрасываем старые сообщения, которые пришли, пока бот был выключен
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logging.exception("Ошибка во время работы бота", exc_info=e)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен!")