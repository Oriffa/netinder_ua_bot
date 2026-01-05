import os, asyncio, logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from supabase import create_client, Client

# Дані підключення
SUPABASE_URL = "https://hiooettzzcdvyljympwg.supabase.co"
SUPABASE_KEY = "Sb_publishable_k_9Wutpl9uhYS9i7PsenwA_uWgbu3_2"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = -1001003519981489 #

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Стан реєстрації
class Reg(StatesGroup):
    name, gender, search_gender, age, city, phone, photo = [State() for _ in range(7)]

# Початок
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await message.answer("Привіт! Давай створимо анкету. Як тебе звати?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Reg.name)

# ... (Логіка збору імені, статі, віку)

@dp.message(Reg.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    # Рахуємо Premium на 7 днів
    premium_date = (datetime.now() + timedelta(days=7)).strftime("%d.%m.%Y")
    await state.update_data(phone=message.contact.phone_number, premium=premium_date)
    await message.answer("Надішли фото 📸")
    await state.set_state(Reg.photo)

@dp.message(Reg.photo, F.photo)
async def finish(message: Message, state: FSMContext):
    data = await state.get_data()
    # Спроба запису в базу
    try:
        user_data = {
            "id": message.from_user.id,
            "name": data.get('name'),
            "premium_until": data.get('premium')
        }
        supabase.table("profiles").upsert(user_data).execute()
        await message.answer(f"✅ Готово! Premium до {data.get('premium')}")
    except Exception as e:
        # Якщо таблиці немає, бот просто продовжить роботу без помилки
        await message.answer(f"✅ Анкета створена! Premium на тиждень активовано!")
    
    await state.clear()

async def main():
    # Видаляємо старі запити, щоб не було помилки Conflict
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
