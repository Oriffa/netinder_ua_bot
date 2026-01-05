import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Створюємо кнопки головного меню
def get_main_menu():
    buttons = [
        [KeyboardButton(text="📝 Створити анкету")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="🔍 Дивитися анкети")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🖤 **Netinder**\n\n"
        "Вітаємо! Тут знайомляться справжні люди.\n"
        "Щоб почати, натисни кнопку нижче 👇",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# Обробка натискання кнопок (поки що просто відповідь)
@dp.message(lambda message: message.text == "📝 Створити анкету")
async def create_profile(message: Message):
    await message.answer("Скоро тут буде покрокова анкета! Готуємо логіку... ⚙️")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
