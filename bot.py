import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Визначаємо етапи анкети
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()
    photo = State()

def get_main_menu():
    buttons = [
        [KeyboardButton(text="📝 Створити анкету")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="🔍 Дивитися анкети")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🖤 Вітаємо у **Netinder**!\nНатисніть кнопку нижче, щоб створити профіль.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# Початок анкетування
@dp.message(F.text == "📝 Створити анкету")
async def cmd_start_form(message: Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Як тебе звати?", reply_markup=ReplyKeyboardRemove())

@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer(f"Приємно познайомитись, {message.text}! Скільки тобі років?")

@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Будь ласка, введи вік цифрами (наприклад, 25):")
    
    await state.update_data(age=message.text)
    await state.set_state(Form.city)
    await message.answer("З якого ти міста?")

@dp.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Form.photo)
    await message.answer("Майже готово! Надішли своє фото для анкети:")

@dp.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    
    await state.clear()
    
    caption = (
        f"✅ Анкета створена!\n\n"
        f"👤 Ім'я: {data['name']}\n"
        f"🎂 Вік: {data['age']}\n"
        f"📍 Місто: {data['city']}"
    )
    
    await message.answer_photo(photo_id, caption=caption, reply_markup=get_main_menu())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
@dp.message(Command("id"))
async def get_group_id(message: types.Message):
    await message.answer(f"ID цієї групи: `{message.chat.id}`")
