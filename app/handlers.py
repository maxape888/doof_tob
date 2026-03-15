import datetime
from aiogram import Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)

from .utils.parser import parse_food_input
from .utils.database import (
    search_foods, 
    get_food_by_id, 
    upsert_user_profile, 
    get_user_profile, 
    log_meal, 
    get_daily_stats,
    get_daily_logs,
    reset_user_data,
    add_custom_food
)

# --- СОСТОЯНИЯ ---
class BotStates(StatesGroup):
    reg_gender = State()   
    reg_age = State()
    reg_height = State()
    reg_weight = State()
    reg_activity = State()
    
    waiting_for_weight = State()    
    collecting_meal = State()       
    waiting_for_meal_name = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_progress_bar(percent):
    length = 12 
    filled_length = int(length * percent / 100)
    display_filled = min(filled_length, length)
    display_empty = max(0, length - display_filled)
    bar = "▬" * display_filled + "▭" * display_empty
    return f"<code>{bar}</code>"

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика за день")],
            [KeyboardButton(text="🍎 Начать запись приема пищи")],
            [KeyboardButton(text="➕ Добавить новый продукт")]
        ],
        resize_keyboard=True
    )

def get_gender_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Мужчина 👦"), KeyboardButton(text="Женщина 👧")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_meal_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟢 Добавить еще"), KeyboardButton(text="✅ Это всё")]
        ],
        resize_keyboard=True
    )

def get_meal_names_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Завтрак 🌅"), KeyboardButton(text="Обед 🍲")],
            [KeyboardButton(text="Ужин 🌙"), KeyboardButton(text="Перекус 🍎")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_activity_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Минимальный (сидячая работа)")],
            [KeyboardButton(text="Низкий (1-3 тренировки в неделю)")],
            [KeyboardButton(text="Средний (3-5 тренировок в неделю)")],
            [KeyboardButton(text="Высокий (6-7 тренировок в неделю)")],
            [KeyboardButton(text="Очень высокий (тяжелая работа/спорт)")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# --- ЛОГИКА РЕГИСТРАЦИИ ХЕНДЛЕРОВ ---

def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_reset, Command("reset"))
    dp.message.register(check_db_content, Command("check"))
    
    # Добавление продуктов
    dp.message.register(cmd_add_food, Command("add_food")) 
    dp.message.register(ask_add_food_instruction, F.text == "➕ Добавить новый продукт")
    
    dp.callback_query.register(cmd_start, F.data == "re_start")
    
    dp.message.register(show_daily_stats_handler, F.text == "📊 Статистика за день")
    dp.message.register(ask_for_food, F.text == "🍎 Начать запись приема пищи")
    
    dp.message.register(process_gender, BotStates.reg_gender)
    dp.message.register(process_age, BotStates.reg_age)
    dp.message.register(process_height, BotStates.reg_height)
    dp.message.register(process_weight, BotStates.reg_weight)
    dp.message.register(process_activity, BotStates.reg_activity)

    dp.message.register(finish_meal, F.text == "✅ Это всё")
    dp.message.register(save_meal_final, BotStates.waiting_for_meal_name)
    dp.message.register(ask_next_item, F.text == "🟢 Добавить еще")
    dp.message.register(process_food_weight, BotStates.waiting_for_weight)
    
    dp.callback_query.register(process_food_selection, F.data.startswith("food_id:"))
    
    dp.message.register(start_or_continue_meal, BotStates.collecting_meal)
    dp.message.register(start_or_continue_meal, F.text)

# --- ОБРАБОТЧИКИ ---

async def ask_add_food_instruction(message: types.Message):
    text = (
        "📝 <b>Добавление своего продукта</b>\n\n"
        "Чтобы внести новый продукт в базу, пришлите сообщение в формате:\n"
        "<code>/add_food Название, Ккал, Белки, Жиры, Углеводы</code>\n\n"
        "<i>Пример:</i>\n"
        "<code>/add_food Домашний блин, 180, 5, 7, 25</code>"
    )
    await message.answer(text, parse_mode="HTML")

async def cmd_add_food(message: types.Message):
    try:
        raw_text = message.text.replace("/add_food", "").strip()
        if not raw_text:
            await ask_add_food_instruction(message)
            return

        parts = [p.strip() for p in raw_text.split(",")]
        if len(parts) != 5:
            await message.answer("❌ Нужно 5 параметров через запятую!\nПример: <code>/add_food Домашний блин, 180, 5, 7, 25</code>", parse_mode="HTML")
            return

        name = parts[0]
        kcal = float(parts[1].replace(",", "."))
        p = float(parts[2].replace(",", "."))
        f = float(parts[3].replace(",", "."))
        c = float(parts[4].replace(",", "."))

        if add_custom_food(name, kcal, p, f, c):
            await message.answer(f"✅ Продукт <b>{name.strip()}</b> добавлен! Теперь можно использовать.", parse_mode="HTML")
        else:
            await message.answer(f"Продукт с таким именем уже есть.", parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Ошибка: Ккал, Б, Ж, У должны быть числами.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")

async def check_db_content(message: types.Message):
    foods = search_foods("а")
    if foods:
        sample = "\n".join([f"🔹 {f['name']} ({f['kcal']} ккал)" for f in foods[:5]])
        await message.answer(f"База найдена! Примеры продуктов:\n{sample}")
    else:
        await message.answer("⚠️ База пуста.")

async def cmd_start(message: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = get_user_profile(user_id)
    is_callback = isinstance(message, types.CallbackQuery)
    target = message.message if is_callback else message

    if user:
        await target.answer(
            f"👋 С возвращением! Ваша норма: <b>{int(user['daily_norm'])} ккал</b>.",
            reply_markup=get_main_kb(), parse_mode="HTML"
        )
    else:
        await target.answer("👋 Привет! Давай рассчитаем твою норму.\nУкажи свой пол:", reply_markup=get_gender_kb())
        await state.set_state(BotStates.reg_gender)
    if is_callback: await message.answer()

async def cmd_reset(message: types.Message, state: FSMContext):
    await state.clear()
    if reset_user_data(message.from_user.id):
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать настройку заново 🚀", callback_data="re_start")]
        ])
        await message.answer("♻️ Данные удалены.", reply_markup=ReplyKeyboardRemove())
        await message.answer("Профиль пуст. Нажмите кнопку ниже, чтобы начать заново:", reply_markup=inline_kb)
    else:
        await message.answer("❌ Ошибка при сбросе.")

async def ask_for_food(message: types.Message):
    await message.answer("Введите название продукта и вес (напр: <i>Курица 200</i>):", 
                         reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

async def start_or_continue_meal(message: types.Message, state: FSMContext):
    name, weight = parse_food_input(message.text)
    if not name: return 
    foods = search_foods(name)
    if not foods:
        await message.reply(f"🤷‍♂️ Продукт «{name}» не найден.")
        return
    if len(foods) == 1:
        food = foods[0]
        await state.update_data(current_food=dict(food))
        if not weight:
            await state.set_state(BotStates.waiting_for_weight)
            await message.answer(f"⚖️ Укажите вес для «{food['name']}» (г):")
        else:
            await add_item_to_meal(message, state, food, weight)
    else:
        keyboard = []
        for f in foods:
            btn_text = f"{f['name'][:30]}... ({int(f['kcal'])} ккал)" if len(f['name']) > 30 else f"{f['name']} ({int(f['kcal'])} ккал)"
            cb_data = f"food_id:{f['id']}:{weight if weight else 0}"
            keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=cb_data)])
        await message.answer("🔍 Выберите вариант:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

async def process_food_selection(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split(":")
    food_id, weight = int(data_parts[1]), float(data_parts[2])
    food = get_food_by_id(food_id)
    if not food: return
    await state.update_data(current_food=dict(food))
    await callback.message.edit_text(f"✅ Выбрано: <b>{food['name']}</b>", parse_mode="HTML")
    if weight == 0:
        await state.set_state(BotStates.waiting_for_weight)
        await callback.message.answer("⚖️ Введите вес (г):")
    else:
        await add_item_to_meal(callback.message, state, food, weight)
    await callback.answer()

async def process_food_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.replace(',', '.'))
        data = await state.get_data()
        await add_item_to_meal(message, state, data['current_food'], weight)
    except:
        await message.answer("Введите числовое значение веса.")

async def add_item_to_meal(message: types.Message, state: FSMContext, food, weight):
    factor = weight / 100.0
    item = {'kcal': food['kcal'] * factor, 'prot': food['protein'] * factor,
            'fat': food['fat'] * factor, 'carb': food['carbs'] * factor,
            'name': food['name'], 'weight': weight}
    data = await state.get_data()
    meal = data.get('meal_list', [])
    meal.append(item)
    await state.update_data(meal_list=meal)
    await state.set_state(BotStates.collecting_meal)
    current_total = sum(x['kcal'] for x in meal)
    await message.answer(f"➕ Добавлено: {food['name']} ({int(weight)}г)\n💰 Итого в приеме: {int(current_total)} ккал", 
                         reply_markup=get_meal_kb())

async def ask_next_item(message: types.Message, state: FSMContext):
    await message.answer("✍️ Введите следующий продукт (напр: <i>Кофе 200</i>):", 
                         reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

async def finish_meal(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if not data.get('meal_list'):
        await message.answer("Вы еще ничего не добавили.", reply_markup=get_main_kb())
        await state.clear()
        return
    await message.answer("Как назовем этот прием пищи?", reply_markup=get_meal_names_kb())
    await state.set_state(BotStates.waiting_for_meal_name)

async def save_meal_final(message: types.Message, state: FSMContext):
    meal_name = message.text
    data = await state.get_data()
    meal = data.get('meal_list', [])
    tk, tp, tf, tc = sum(x['kcal'] for x in meal), sum(x['prot'] for x in meal), \
                     sum(x['fat'] for x in meal), sum(x['carb'] for x in meal)
    details = ", ".join([f"{x['name']} ({int(x['weight'])}г)" for x in meal])
    log_meal(message.from_user.id, tk, tp, tf, tc, details, meal_name)
    user = get_user_profile(message.from_user.id)
    stats = get_daily_stats(message.from_user.id)
    total_today = stats['total_kcal'] if (stats and stats['total_kcal']) else tk
    norm = user['daily_norm'] if user else 2000
    res = f"🍽 <b>{meal_name}</b> записан!\n🔥 Всего за прием: {int(tk)} ккал\n"
    res += f"\n⚠️ Превышение!" if total_today > norm else f"\n✅ Осталось {int(norm - total_today)} ккал."
    await message.answer(res, parse_mode="HTML", reply_markup=get_main_kb())
    await state.clear()

async def show_daily_stats_handler(message: types.Message):
    user_id = message.from_user.id
    stats = get_daily_stats(user_id)
    user = get_user_profile(user_id)
    logs = get_daily_logs(user_id)

    if not user:
        await message.answer("⚠️ Рассчитайте норму через /start")
        return

    if not stats or stats['total_kcal'] is None:
        await message.answer("Запишите первый прием пищи! 🍎")
        return

    norm = user['daily_norm']
    total_kcal = stats['total_kcal'] or 0
    total_prot = stats['total_prot'] or 0
    total_fat = stats['total_fat'] or 0
    total_carb = stats['total_carb'] or 0

    percent = (total_kcal / norm) * 100 if norm > 0 else 0

    text = f"📊 <b>СТАТИСТИКА ЗА СЕГОДНЯ</b>\n\n"

    if logs:
        for log in logs:
            what_ate = log['details'] if log['details'] else "Продукт не указан"

            text += f"🕒 <code>{log['meal_time']}</code> <b>{log['meal_name']}</b>\n"
            text += f"   Что съедено: {what_ate}\n"
            text += f"   🔥 {log['kcal']:.0f} ккал | "
            text += f"🥩 {log['protein']:.1f} г | "
            text += f"🧈 {log['fat']:.1f} г | "
            text += f"🍞 {log['carbs']:.1f} г\n\n"

        text += "────────────────────────────\n"

    # Итог дня — используем точные суммы из stats, без повторного округления
    text += f"🥩 <b>Б:</b> {total_prot:.1f} г | "
    text += f"🥑 <b>Ж:</b> {total_fat:.1f} г | "
    text += f"🍞 <b>У:</b> {total_carb:.1f} г\n\n"
    text += f"🔥 <b>Итог:</b> {total_kcal:.0f} / {norm:.0f} ккал\n"
    text += f"{get_progress_bar(percent)} <b>{percent:.0f}%</b>"

    await message.answer(text, parse_mode="HTML")
async def process_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Введите ваш возраст:")
    await state.set_state(BotStates.reg_age)

async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Введите ваш рост (см):")
    await state.set_state(BotStates.reg_height)

async def process_height(message: types.Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.answer("Введите ваш вес (кг):")
    await state.set_state(BotStates.reg_weight)

async def process_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer("Выберите уровень активности:", reply_markup=get_activity_kb())
    await state.set_state(BotStates.reg_activity)

async def process_activity(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        weight = float(data['weight'])
        height = float(data['height'])
        age = int(data['age'])
        bmr = (10 * weight) + (6.25 * height) - (5 * age)
        bmr = bmr + 5 if data['gender'] == "Мужчина 👦" else bmr - 161
        act_map = {"Минимальный (сидячая работа)": 1.2, "Низкий (1-3 тренировки в неделю)": 1.375,
                   "Средний (3-5 тренировок в неделю)": 1.55, "Высокий (6-7 тренировок в неделю)": 1.725,
                   "Очень высокий (тяжелая работа/спорт)": 1.9}
        daily_norm = int(bmr * act_map.get(message.text, 1.2))
        height_m = height / 100
        bmi = round(weight / (height_m ** 2), 1)
        if bmi < 18.5: status = "ниже нормы 🦴"
        elif 18.5 <= bmi < 25: status = "в норме ✅"
        elif 25 <= bmi < 30: status = "избыточный ⚠️"
        else: status = "ожирение 🚨"
        upsert_user_profile(message.from_user.id, data['gender'], age, height, weight, message.text, daily_norm)
        res = (f"✅ <b>Профиль настроен!</b>\n\n📊 ИМТ: <b>{bmi}</b> ({status})\n🔥 Норма: <b>{daily_norm} ккал</b>")
        await message.answer(res, reply_markup=get_main_kb(), parse_mode="HTML")
        await state.clear()
    except Exception as e:
        await message.answer("Ошибка в расчетах. Попробуйте /start.")
        await state.clear()
