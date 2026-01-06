import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from supabase import create_client

# --- НАЛАШТУВАННЯ ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ціна в зірках (наприклад, 100 зірок)
PREMIUM_PRICE = 100

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer(
        f"Привіт! Оформіть доступ за {PREMIUM_PRICE} зірок ⭐️",
        reply_markup=payment_keyboard()
    )

def payment_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(
        text=f"Оплатити {PREMIUM_PRICE} зірок", 
        pay=True)
    )
    return keyboard

@dp.message_handler(commands=['pay'])
async def send_invoice(message: types.Message):
    await bot.send_invoice(
        message.chat.id,
        title="Преміум доступ",
        description="Повний доступ на 30 днів",
        provider_token="", # Для зірок залишаємо порожнім
        currency="XTR",
        prices=[types.LabeledPrice(label="Преміум", amount=PREMIUM_PRICE)],
        payload="premium_subscription"
    )

@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=types.ContentTypes.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    # Додаємо 30 днів до поточної дати
    new_date = (datetime.now() + timedelta(days=30)).isoformat()
    user_id = str(message.from_user.id)

    # Записуємо в Supabase (Таблиця "profiles")
    try:
        supabase.table("profiles").upsert({
            "id": user_id,
            "premium_data": new_date
        }).execute()
        
        await message.answer("Оплата успішна! Ваш доступ оновлено на 30 днів.")
    except Exception as e:
        await message.answer("Оплата пройшла, але виникла помилка в базі даних. Зв'яжіться з адміном.")
        print(f"Error: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
