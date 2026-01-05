import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАЛАШТУВАННЯ ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = -1001003519981489  # Твоя група для скарг та статистики

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    phone = State()
    name = State()
    gender = State()
    search_gender = State()
    age = State()
    city = State()
    photo = State()

class ReportState(StatesGroup):
    choosing_reason = State()
    waiting_for_details = State()

# --- МЕНЮ ---
def main_menu():
    kb = [
        [KeyboardButton(text="🔍 Дивитись анкети"), KeyboardButton(text="❤️ Мене лайкнули")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="⭐ Premium")],
        [KeyboardButton(text="🆘 Зв'язок з адміном")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- СТАРТ ТА ПРИВАТНІСТЬ НОМЕРА ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    welcome_text = (
        "Вітаємо у **Нетіндер** 🖤\n\n"
        "Тут знайомляться без ілюзій. Ми цінуємо твій спокій, тому просимо підтвердити особу.\n\n"
        "🛡 **Про приватність:**\n"
        "— Твій номер бачимо лише ми для захисту від фейків.\n"
        "— **Ми ніколи не передаємо його третім особам.**\n"
        "— **Ми ніколи не будемо тобі дзвонити.**\n\n"
        "Перший тиждень після реєстрації — **Premium безкоштовно!** 🎁"
    )
    await message.answer(
        welcome_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Надати номер 📱", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await state.set_state(Form.phone)

# --- РЕЄСТРАЦІЯ ТА СПОВІЩЕННЯ ПРО НОВОГО КОРИСТУВАЧА ---
@dp.message(Form.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Дякуємо за довіру! Тепер скажи, як тебе звати?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.name)

@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = [[KeyboardButton(text="Я Чоловік 👨"), KeyboardButton(text="Я Жінка 👩")]]
    await message.answer("Твоя стать:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Form.gender)

@dp.message(Form.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    kb = [[KeyboardButton(text="Шукаю Чоловіка 👨"), KeyboardButton(text="Шукаю Жінку 👩")]]
    await message.answer("Кого ти шукаєш?", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Form.search_gender)

@dp.message(Form.search_gender)
async def process_search(message: Message, state: FSMContext):
    await state.update_data(search_gender=message.text)
    await message.answer("Скільки тобі років?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.age)

@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("З якого ти міста?")
    await state.set_state(Form.city)

@dp.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Надішли своє фото.")
    await state.set_state(Form.photo)

@dp.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    # СПОВІЩЕННЯ В ГРУПУ АДМІНУ
    admin_msg = (
        f"🆕 **Нова реєстрація!**\n"
        f"👤 Ім'я: {data.get('name')}, {data.get('age')}р.\n"
        f"📍 Місто: {data.get('city')}\n"
        f"📱 Номер: {data.get('phone')}\n"
        f"🆔 ID: `{message.from_user.id}`"
    )
    await bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_msg)
    
    await message.answer("Анкета створена! Бажаємо вдалих знайомств. 😉", reply_markup=main_menu())
    await state.clear()

# --- СТАТИСТИКА (ТІЛЬКИ ДЛЯ ГРУПИ АДМІНІВ) ---
@dp.message(Command("stats"))
async def get_stats(message: Message):
    if message.chat.id == ADMIN_GROUP_ID:
        # У майбутньому тут буде запит до бази даних
        await message.answer("📊 **Статистика «Нетіндер»**\n\n👥 Користувачів: 1 (ти)\n💎 Premium: 1\n🆕 За сьогодні: +1")

# --- ЛОГІКА СКАРГ (БЕЗ ЗМІН) ---
@dp.callback_query(F.data == "report_user_btn")
async def report_user_start(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Фейк", callback_data="reason_fake")],
        [InlineKeyboardButton(text="🔞 Пошлість", callback_data="reason_nsfw")],
        [InlineKeyboardButton(text="😤 Образи", callback_data="reason_abuse")],
        [InlineKeyboardButton(text="🚫 Інше", callback_data="reason_other")]
    ])
    await callback.message.answer("Оберіть причину:", reply_markup=kb)
    await state.set_state(ReportState.choosing_reason)

@dp.callback_query(F.data.startswith("reason_"))
async def report_reason_step(callback: types.CallbackQuery, state: FSMContext):
    reason = callback.data.split("_")[1]
    await state.update_data(current_reason=reason)
    await callback.message.answer("Деталі скарги? (або '-')")
    await state.set_state(ReportState.waiting_for_details)

@dp.message(ReportState.waiting_for_details)
async def report_final(message: Message, state: FSMContext):
    data = await state.get_data()
    report_text = (
        f"🚨 **СКАРГА**\n"
        f"👤 Від: {message.from_user.id}\n"
        f"❓ Причина: {data['current_reason']}\n"
        f"📝 Деталі: {message.text}"
    )
    await bot.send_message(chat_id=ADMIN_GROUP_ID, text=report_text)
    await message.answer("Скаргу надіслано.", reply_markup=main_menu())
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
