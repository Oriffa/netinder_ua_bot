import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import LabeledPrice, PreCheckoutQuery
from supabase import create_client

# --- НАЛАШТУВАННЯ ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ціна в зірках (наприклад, 100 зірок)
PREMIUM_STARS_PRICE = 100

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_id
    premium_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Реєстрація (upsert оновить, якщо вже є)
    data = {"id": user_id, "name": message.from_user.first_name, "premium_until": premium_date}
    supabase.table("profiles").upsert(data).execute()
    
    await message.answer(f"🚀 Тобі активовано 7 днів Premium до {premium_date}!")

@dp.message_handler(lambda message: message.text == "💳 Купити Premium")
async def pay_stars(message: types.Message):
    await bot.send_invoice(
        message.chat.id,
        title="Premium доступ на 30 днів",
        description="Повний доступ до пошуку анкет",
        provider_token="", # Для Stars залишаємо порожнім
        currency="XTR",    # Код валюти для Telegram Stars
        prices=[LabeledPrice(label="Premium", amount=PREMIUM_STARS_PRICE)],
        payload="premium_30_days"
    )

@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def success_payment(message: types.Message):
    # Додаємо 30 днів до поточної дати
    new_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    supabase.table("profiles").update({"premium_until": new_date}).eq("id", message.from_id).execute()
    
    await message.answer(f"✅ Оплата успішна! Твій Premium подовжено до {new_date}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
