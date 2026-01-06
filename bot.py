import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery
from supabase import create_client, Client
from aiohttp import web

# --- НАЛАШТУВАННЯ WEB-СЕРВЕРА ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render передає порт у змінну оточення PORT
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

# --- НАЛАШТУВАННЯ БОТА ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привіт! Оплатіть доступ до преміум-функцій (10 зірок):",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="Оплатити 10 ⭐", pay=True)
        ]])
    )

@dp.shipping_query()
async def shipping_handler(query: types.ShippingQuery):
    await bot.answer_shipping_query(query.id, ok=True)

@dp.pre_checkout_query()
async def checkout_handler(checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(checkout_query.id, ok=True)

@dp.message(lambda message: message.successful_payment is not None)
async def got_payment(message: types.Message):
    user_id = str(message.from_user.id)
    # Записуємо в Supabase
    supabase.table("profiles").upsert({"id": user_id, "premium_data": "active"}).execute()
    await message.answer("Дякуємо! Ваш преміум-доступ активовано.")

async def main():
    # Запускаємо веб-сервер паралельно з ботом
    asyncio.create_task(start_web_server())
    # Запускаємо бота
    print("Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
