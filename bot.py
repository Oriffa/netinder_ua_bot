import os
import asyncio
import logging
import http.server
import socketserver
import threading
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- ФЕЙКОВИЙ СЕРВЕР ДЛЯ БЕЗКОШТОВНОГО RENDER ---
def run_dummy_server():
    handler = http.server.SimpleHTTPRequestHandler
    # Render використовує порт 10000 за замовчуванням
    with socketserver.TCPServer(("", 10000), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- НАЛАШТУВАННЯ ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = -1001003519981489  # Твоя група Нетіндер адмінка

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    phone, name, gender, search_gender, age, city, photo = State(), State(), State(), State(), State(), State(), State()

class ReportState(StatesGroup):
    current_reason, waiting_for_details = State(), State()

# --- МЕНЮ ---
def main_menu():
    kb = [
        [KeyboardButton(text="🔍 Дивитись анкети"), KeyboardButton(text="❤️ Мене лайкнули")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="⭐ Premium")],
        [KeyboardButton(text="🆘 Зв'язок з адміном")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- РЕЄСТРАЦІЯ (ВИПРАВЛЕНИЙ ТЕКСТ) ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    welcome_text = (
        "Вітаємо у **Нетіндер** 🖤\n\n"
        "Ми створили цей простір для комфортних та щирих знайомств. "
        "Будь ласка, поважай своїх співрозмовників.\n\n"
        "🛡 **Про твій номер телефону:**\n"
        "— Він потрібен виключно для захисту від фейків.\n"
        "— **Ми нікому не передаємо твій номер і ніколи не будемо тобі дзвонити.**\n\n"
        "🎁 Твій перший тиждень — **Premium безкоштовно!**"
    )
    await message.answer(welcome_text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Надати номер 📱", request_contact=True)]], resize_keyboard=True))
    await state.set_state(Form.phone)

@dp.message(Form.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Дякуємо! Тепер скажи, як тебе звати?", reply_markup=ReplyKeyboardRemove())
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
    # Сповіщення в адмінку
    admin_card = (f"🆕 **Нова реєстрація!**\n"
                  f"👤 {data['name']}, {data['age']}р., {data['city']}\n"
                  f"🚻 Стать: {data['gender']}\n"
                  f"📱 Номер: {data['phone']}\n"
                  f"🆔 ID: `{message.from_user.id}`")
    await bot.send_photo(chat_id=ADMIN_GROUP_ID, photo=message.photo[-1].file_id, caption=admin_card)
    await message.answer("Анкета створена! Приємних знайомств. 😉", reply_markup=main_menu())
    await state.clear()

# --- СТАТИСТИКА (ТІЛЬКИ В ГРУПІ) ---
@dp.message(Command("stats"), F.chat.id == ADMIN_GROUP_ID)
async def cmd_stats(message: Message):
    await message.answer("📊 **Статистика «Нетіндер»**\n\n👥 Всього: 1\n👨 Чоловіків: 0\n👩 Жінок: 1\n💎 Premium: 1")

# --- СКАРГИ ---
@dp.callback_query(F.data.startswith("reason_"))
async def report_desc(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_reason=callback.data.split("_")[1])
    await callback.message.answer("Опиши деталі? (Або '-')")
    await state.set_state(ReportState.waiting_for_details)

@dp.message(ReportState.waiting_for_details)
async def report_final(message: Message, state: FSMContext):
    data = await state.get_data()
    report = (f"🚨 **СКАРГА**\
