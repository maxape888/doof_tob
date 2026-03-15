import sys
import os
import asyncio
import logging

# Добавляем путь, чтобы Python видел папку app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

# Импортируем хендлеры и планировщик
from app.handlers import register_handlers
from app.utils.scheduler import setup_scheduler

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# --- БЕЗОПАСНОСТЬ И НАСТРОЙКИ ---
# Теперь бот сначала ищет токен в переменных окружения (для GitHub/Railway),
# а если не находит — пытается взять из твоего файла config.py
try:
    from config import BOT_TOKEN
except ImportError:
    BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logging.error("Ошибка: Токен бота не найден! Установите переменную BOT_TOKEN.")
    sys.exit(1)

# Создаем папку data, если её нет (важно для базы данных в облаке)
if not os.path.exists("data"):
    os.makedirs("data")
    logging.info("Папка 'data' создана.")

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота / Проверить норму"),
        BotCommand(command="reset", description="Сбросить все данные и анкету"),
    ]
    await bot.set_my_commands(commands)

async def main():
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация хендлеров
    register_handlers(dp)

    # Установка меню команд
    await set_commands(bot)

    # Настройка планировщика
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logging.info("Планировщик напоминаний запущен!")

    logging.info("Бот успешно запущен и готов к работе!")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logging.exception("Ошибка при запуске бота", exc_info=e)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен!")