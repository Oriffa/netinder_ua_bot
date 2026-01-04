import os
from aiogram import Bot, Dispatcher, types, executor


TOKEN = os.getenv("TELEGRAM_TOKEN")
BAD_WORDS = ["секс", "хуй", "інтим"] 

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Вітаємо у Нетіндер! 📸 Надішли своє фото (НЕ переслане).")

@dp.message_handler(content_types=['photo'])
async def check_photo(message: types.Message):
    if message.forward_from or message.forward_from_chat:
        await message.answer("❌ Фейки заборонені. Надішліть фото безпосередньо.")
    else:
        await message.answer("✅ Фото прийнято. Тепер напиши опис про себе (без пошлості).")

@dp.message_handler()
async def check_text(message: types.Message):
    
    if any(word in message.text.lower() for word in BAD_WORDS):
        await message.answer("❌ Твій опис порушує правила (пошлість). Виправ його.")
    else:
        await message.answer("✅ Анкета збережена! Твій рівень: 1.")

if __name__ == '__main__':
    executor.start_polling(dp)
