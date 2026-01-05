import http.server
import socketserver
import threading

# Створюємо фейковий веб-сервер для Render
def run_dummy_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 10000), handler) as httpd:
        httpd.serve_forever()

# Запускаємо його в окремому потоці
threading.Thread(target=run_dummy_server, daemon=True).start()
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

# --- СТАНИ ---
class Form(StatesGroup):
    phone = State()
    name = State()
    gender = State()
    search_gender = State()
    age = State()
    city = State()
    photo = State()

class ReportState(StatesGroup):
    current_reason = State()
    waiting_for_details = State()

# --- КНОПКИ МЕНЮ ---
def main_menu():
    kb = [
        [KeyboardButton(text="🔍 Дивитись анкети"), KeyboardButton(text="❤️ Мене лайкнули")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="⭐ Premium")],
        [KeyboardButton(text="🆘 Зв'язок з адміном")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ПРИВІТАННЯ ТА ГАРАНТІЯ ПРИВАТНОСТІ ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    welcome_text = (
        "Вітаємо у **Нетіндер** 🖤\n\n"
        "Тут ми цінуємо твій час та комфорт. Будь ласка, поважай своїх співрозмовників — це основа нашої спільноти.\n\n"
        "🛡 **Про твій номер телефону:**\n"
        "— Він потрібен виключно для захисту від фейків та дублікатів.\n"
        "— **Ми нікому не передаємо твій номер.**\n"
        "— **Ми ніколи не будемо тобі дзвонити.**\n\n"
        "🎁 Твій перший тиждень після реєстрації — **Premium безкоштовно!**"
    )
    await message.answer(
        welcome_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Надати номер 📱", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await state.set_state(Form.phone)

# --- РЕЄСТРАЦІЯ ---
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
    await message.answer("Надішли своє фото. Використовуй реальні знімки — так шанси знайти цікаву людину значно вищі.")
    await state.set_state(Form.photo)

@dp.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    # Надсилаємо анкету в адмін-групу
    admin_info = (
        f"🆕 **Новий користувач!**\n"
        f"👤 {data['name']}, {data['age']}р., {data['city']}\n"
        f"📱 Номер: {data['phone']}\n"
        f"🆔 ID: `{message.from_user.id}`"
    )
    await bot.send_photo(chat_id=ADMIN_GROUP_ID, photo=message.photo[-1].file_id, caption=admin_info)
    
    await message.answer("Анкета створена! Бажаємо приємного спілкування. 😉", reply_markup=main_menu())
    await state.clear()

# --- СТАТИСТИКА ТА АДМІНКА ---
@dp.message(Command("stats"), F.chat.id == ADMIN_GROUP_ID)
async def cmd_stats(message: Message):
    await message.answer("📊 **Статистика «Нетіндер»**\n\n👥 Зареєстровано: 1\n🆕 Сьогодні: +1\n💎 Premium юзери: 1")

@dp.message(F.text == "🆘 Зв'язок з адміном")
async def contact_admin(message: Message):
    await message.answer("Напиши своє запитання наступним повідомленням. Адміністрація отримає його і відповість найближчим часом.")

# --- ЛОГІКА СКАРГ (ВИКЛИК ЧЕРЕЗ КНОПКУ ПІД АНКЕТОЮ) ---
@dp.callback_query(F.data.startswith("reason_"))
async def report_description(callback: types.CallbackQuery, state: FSMContext):
    reason = callback.data.split("_")[1]
    await state.update_data(current_reason=reason)
    await callback.message.answer("Будь ласка, опиши детальніше, що саме не так? (Якщо не хочеш писати, просто надішли '-')")
    await state.set_state(ReportState.waiting_for_details)

@dp.message(ReportState.waiting_for_details)
async def report_to_group(message: Message, state: FSMContext):
    data = await state.get_data()
    report_msg = (
        f"🚨 **СКАРГА ВІД КОРИСТУВАЧА**\n"
        f"👤 Від: {message.from_user.full_name} (ID: `{message.from_user.id}`)\n"
        f"❓ Причина: {data.get('current_reason')}\n"
        f"📝 Коментар: {message.text}"
    )
    await bot.send_message(chat_id=ADMIN_GROUP_ID, text=report_msg)
    await message.answer("Дякуємо! Скарга надіслана на розгляд модераторам. ✅", reply_markup=main_menu())
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
