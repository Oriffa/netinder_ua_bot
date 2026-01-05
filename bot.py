import os
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from supabase import create_client, Client

# --- НАЛАШТУВАННЯ ---
# Дані з твоїх скріншотів
SUPABASE_URL = "https://hiooettzzcdvyljympwg.supabase.co"
SUPABASE_KEY = "Sb_publishable_k_9Wutpl9uhYS9i7PsenwA_uWgbu3_2"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = -1001003519981489 # Твоя група адмінки

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Стан реєстрації
class Reg(StatesGroup):
    name = State()
    gender = State()
    search_gender = State()
    age = State()
    city = State()
    phone = State()
    photo = State()

# --- ГОЛОВНЕ МЕНЮ ---
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔍 Пошук"), KeyboardButton(text="👤 Профіль")],
        [KeyboardButton(text="💡 Ідея для бота")]
    ], resize_keyboard=True)

# --- ЛОГІКА БОТА ---

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Вітаємо у **Нетіндер** 🖤\n\nДавай створимо твою анкету. Як тебе звати?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Reg.name)

@dp.message(Reg.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Я Чоловік 👨"), KeyboardButton(text="Я Жінка 👩")]
    ], resize_keyboard=True)
    await message.answer("Твоя стать:", reply_markup=kb)
    await state.set_state(Reg.gender)

@dp.message(Reg.gender)
async def reg_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Шукаю Чоловіків 👨"), KeyboardButton(text="Шукаю Жінок 👩")]
    ], resize_keyboard=True)
    await message.answer("Кого ти хочеш бачити в пошуку?", reply_markup=kb)
    await state.set_state(Reg.search_gender)

@dp.message(Reg.search_gender)
async def reg_search(message: Message, state: FSMContext):
    await state.update_data(search_gender=message.text)
    await message.answer("Скільки тобі років?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Reg.age)

@dp.message(Reg.age)
async def reg_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Будь ласка, введи вік числом.")
    await state.update_data(age=int(message.text))
    await message.answer("З якого ти міста?")
    await state.set_state(Reg.city)

@dp.message(Reg.city)
async def reg_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Надати номер ✅", request_contact=True)],
        [KeyboardButton(text="Пропустити ➡️")]
    ], resize_keyboard=True)
    await message.answer("🛡 **Верифікація**\n\nНадай номер для статусу ✅. Це підвищує довіру!", reply_markup=kb)
    await state.set_state(Reg.phone)

@dp.message(Reg.phone)
@dp.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    verified = True if message.contact else False
    phone = message.contact.phone_number if message.contact else "Приховано"
    
    # ПРЕМІУМ НА 7 ДНІВ
    premium_date = (datetime.now() + timedelta(days=7)).strftime("%d.%m.%Y")
    await state.update_data(phone=phone, verified=verified, premium=premium_date)
    
    await message.answer("Надішли своє найкраще фото 📸", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Reg.photo)

@dp.message(Reg.photo, F.photo)
async def reg_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id

    # Спроба збереження в Supabase
    try:
        user_record = {
            "id": user_id,
            "name": data['name'],
            "age": data['age'],
            "gender": data['gender'],
            "search_gender": data['search_gender'],
            "city": data['city'],
            "phone": data['phone'],
            "is_verified": data['verified'],
            "premium_until": data['premium'],
            "photo_id": photo_id
        }
        # Використовуємо .upsert(), щоб оновлювати анкету, якщо вона вже є
        supabase.table("profiles").upsert(user_record).execute()
        
        status = "✅ Верифікований" if data['verified'] else "👤 Неверифікований"
        
        # Відправка в адмін-групу
        admin_card = (f"🆕 **АНКЕТА В БАЗІ**\n👤 {data['name']}, {data['age']}р.\n"
                     f"📍 {data['city']}\n📱 {data['phone']}\n💎 Premium до: {data['premium']}")
        await bot.send_photo(ADMIN_GROUP_ID, photo=photo_id, caption=admin_card)

        await message.answer(
            f"Готово! 🎉\nСтатус: {status}\n"
            f"💎 **Premium активовано на тиждень!** (до {data['premium']})",
            reply_markup=main_kb()
        )
    except Exception as e:
        logging.error(f"Помилка бази: {e}")
        await message.answer("Анкету створено тимчасово (помилка бази).", reply_markup=main_kb())
    
    await state.clear()

# Обробка ідей
@dp.message(F.text == "💡 Ідея для бота")
async def idea_msg(message: Message):
    await message.answer("Напиши свою ідею наступним повідомленням. Адмін її прочитає!")

# Основна функція запуску
async def main():
    # drop_pending_updates=True прибирає помилку Conflict
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
