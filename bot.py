import os, asyncio, logging, http.server, socketserver, threading
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- ФЕЙКОВИЙ СЕРВЕР ДЛЯ RENDER (БЕЗКОШТОВНИЙ ТАРИФ) ---
def run_dummy_server():
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", 10000), handler) as httpd:
            httpd.serve_forever()
    except Exception: pass

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- НАЛАШТУВАННЯ ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = -1001003519981489 #

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    name, gender, search_gender, age, age_range, city, phone, photo = [State() for _ in range(8)]

class AdminContact(StatesGroup):
    waiting_for_message = State()

# --- ГОЛОВНЕ МЕНЮ ---
def main_menu():
    kb = [
        [KeyboardButton(text="🔍 Пошук анкет"), KeyboardButton(text="❤️ Лайки")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="💡 Запропонувати ідею")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- РЕЄСТРАЦІЯ ТА ВЕРИФІКАЦІЯ ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    welcome_text = (
        "Вітаємо у **Нетіндер** 🖤\n\n"
        "Давай створимо твою анкету. Як тебе звати?"
    )
    await message.answer(welcome_text, reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.name)

# ... (тут логіка name, gender, age_range як у попередньому коді) ...

@dp.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    kb = [
        [KeyboardButton(text="Підтвердити номер ✅", request_contact=True)],
        [KeyboardButton(text="Пропустити ➡️")]
    ]
    await message.answer(
        "🛡 **Верифікація:**\n\n"
        "Ти можеш надати номер телефону. Ми його не публікуємо, але ти отримаєш статус ✅ **Верифікований**.\n"
        "До таких людей набагато більше довіри!",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.set_state(Form.phone)

@dp.message(Form.phone)
@dp.message(Form.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    verified = False
    if message.contact:
        verified = True
        await state.update_data(phone=message.contact.phone_number, verified=True)
    else:
        await state.update_data(phone="Приховано", verified=False)
    
    await message.answer("Завантаж своє фото:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.photo)

@dp.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    status = "✅ ВЕРИФІКОВАНИЙ" if data.get('verified') else "👤 НЕВЕРИФІКОВАНИЙ"
    
    # Сповіщення в адмінку
    admin_msg = (
        f"🆕 **НОВА АНКЕТА**\n"
        f"👤 {data['name']}, {data['age']}р. ({status})\n"
        f"📍 Місто: {data['city']}\n"
        f"🔍 Шукає: {data['search_gender']} ({data['age_range']} років)\n"
        f"🆔 ID: `{message.from_user.id}`"
    )
    await bot.send_photo(chat_id=ADMIN_GROUP_ID, photo=message.photo[-1].file_id, caption=admin_msg)
    await message.answer(f"Готово! Твій статус: {status}", reply_markup=main_menu())
    await state.clear()

# --- ЗВ'ЯЗОК З АДМІНОМ (ПРОПОЗИЦІЇ) ---
@dp.message(F.text == "💡 Запропонувати ідею")
async def contact_admin_start(message: Message, state: FSMContext):
    await message.answer(
        "Напиши свою пропозицію або ідею одним повідомленням. Адмін обов'язково її прочитає! 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Скасувати")]], resize_keyboard=True)
    )
    await state.set_state(AdminContact.waiting_for_message)

@dp.message(AdminContact.waiting_for_message)
async def forward_to_admin(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await message.answer("Повернулися в меню.", reply_markup=main_menu())
        await state.clear()
        return

    # Відправляємо адміну в групу
    suggestion_msg = (
        f"💡 **НОВА ПРОПОЗИЦІЯ**\n"
        f"👤 Від: {message.from_user.full_name} (ID: `{message.from_user.id}`)\n"
        f"📝 Текст: {message.text}"
    )
    await bot.send_message(chat_id=ADMIN_GROUP_ID, text=suggestion_msg)
    
    await message.answer("Дякуємо! Твою ідею надіслано адміну. Ви робите Нетіндер кращим! 🙌", reply_markup=main_menu())
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
