import os, asyncio, logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from supabase import create_client, Client

# --- НАЛАШТУВАННЯ SUPABASE ---
SUPABASE_URL = "https://hiooettzzcdvyljympwg.supabase.co"
SUPABASE_KEY = "Sb_publishable_k_9Wutpl9uhYS9i7PsenwA_uWgbu3_2"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- НАЛАШТУВАННЯ TELEGRAM ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = -1001003519981489 #

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Reg(StatesGroup):
    name = State()
    gender = State()
    search_gender = State()
    age = State()
    age_range = State()
    city = State()
    phone = State()
    photo = State()

# --- МЕНЮ ---
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔍 Пошук"), KeyboardButton(text="👤 Профіль")],
        [KeyboardButton(text="💡 Ідея для бота")]
    ], resize_keyboard=True)

# --- ПОЧАТОК ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await message.answer("Привіт! Створимо анкету в **Нетіндер** 🖤\n\nЯк тебе звати?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Reg.name)

@dp.message(Reg.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = [[KeyboardButton(text="Я Чоловік 👨"), KeyboardButton(text="Я Жінка 👩")]]
    await message.answer("Твоя стать:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Reg.gender)

@dp.message(Reg.gender)
async def reg_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    kb = [[KeyboardButton(text="Шукаю Чоловіків 👨"), KeyboardButton(text="Шукаю Жінок 👩")]]
    await message.answer("Кого ти хочеш бачити в пошуку?", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Reg.search_gender)

@dp.message(Reg.search_gender)
async def reg_search(message: Message, state: FSMContext):
    await state.update_data(search_gender=message.text)
    await message.answer("Який вік тебе цікавить? (наприклад: 18-25)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Reg.age_range)

@dp.message(Reg.age_range)
async def reg_range(message: Message, state: FSMContext):
    await state.update_data(age_range=message.text)
    await message.answer("А скільки років тобі?")
    await state.set_state(Reg.age)

@dp.message(Reg.age)
async def reg_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Твоє місто?")
    await state.set_state(Reg.city)

@dp.message(Reg.city)
async def reg_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    kb = [[KeyboardButton(text="Надати номер ✅", request_contact=True)], [KeyboardButton(text="Пропустити ➡️")]]
    await message.answer("🛡 **Верифікація**\n\nНадай номер через кнопку для статусу ✅.\nПрофілі без номера мають менше довіри.", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Reg.phone)

@dp.message(Reg.phone)
@dp.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    verified = True if message.contact else False
    phone = message.contact.phone_number if message.contact else "Приховано"
    
    # PREMIUM НА ТИЖДЕНЬ (7 днів)
    premium_expiry = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    await state.update_data(phone=phone, verified=verified, premium=premium_expiry)
    
    await message.answer("Надішли своє фото 📸", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Reg.photo)

@dp.message(Reg.photo, F.photo)
async def reg_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id

    # ЗБЕРЕЖЕННЯ В SUPABASE
    user_record = {
        "id": user_id,
        "name": data['name'],
        "age": int(data['age']),
        "gender": data['gender'],
        "search_gender": data['search_gender'],
        "search_age_range": data['age_range'],
        "city": data['city'],
        "phone": data['phone'],
        "is_verified": data['verified'],
        "premium_until": data['premium'],
        "photo_id": photo_id
    }
    
    try:
        supabase.table("profiles").upsert(user_record).execute()
        status = "✅ Верифікований" if data['verified'] else "👤 Неверифікований"
        
        # Повідомлення адміну
        admin_info = f"🆕 **АНКЕТА В БАЗІ**\n👤 {data['name']}, {data['age']}р.\n📱 {data['phone']}\n💎 Premium до: {data['premium']}"
        await bot.send_photo(ADMIN_GROUP_ID, photo=photo_id, caption=admin_info)

        await message.answer(
            f"Готово! 🎉\nСтатус: {status}\n"
            f"💎 **Premium активовано на тиждень!** (до {data['premium']})",
            reply_markup=main_kb()
        )
    except Exception as e:
        await message.answer("Помилка при збереженні. Спробуй пізніше.")
        print(f"Помилка бази: {e}")
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
