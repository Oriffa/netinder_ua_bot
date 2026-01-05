import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАЛАШТУВАННЯ ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = -1001003519981489  # Твоя група для скарг

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- СТАНИ ---
class Form(StatesGroup):
    phone = State()
    name = State()
    gender = State()
    search_gender = State()
    age = State()
    city = State()
    photo = State()

class ReportState(StatesGroup):
    choosing_reason = State()
    waiting_for_details = State()

# --- КНОПКИ ГОЛОВНОГО МЕНЮ ---
def main_menu():
    kb = [
        [KeyboardButton(text="🔍 Дивитись анкети"), KeyboardButton(text="❤️ Мене лайкнули")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="⭐ Premium")],
        [KeyboardButton(text="🆘 Зв'язок з адміном")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- СТАРТ ТА РЕЄСТРАЦІЯ ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Вітаємо у **Нетіндер** 🖤\n\n"
        "Тут знайомляться без ілюзій. Будь ласка, поважай своїх співрозмовників.\n"
        "🎁 Твій перший тиждень — **Premium безкоштовно!**\n\n"
        "Для початку поділися номером телефону (кнопка внизу), щоб ми знали, що ти не фейк.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Надати номер 📱", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await state.set_state(Form.phone)

@dp.message(Form.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    # Тут логіка: один номер - одна реєстрація (перевірка в БД додається при підключенні бази)
    await message.answer("Як тебе звати?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.name)

@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = [[KeyboardButton(text="Я Чоловік 👨"), KeyboardButton(text="Я Жінка 👩")]]
    await message.answer("Твоя стать:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Form.gender)

@dp.message(Form.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    kb = [[KeyboardButton(text="Шукаю Чоловіка 👨"), KeyboardButton(text="Шукаю Жінку 👩")]]
    await message.answer("Кого ти шукаєш?", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Form.search_gender)

@dp.message(Form.search_gender)
async def process_search(message: Message, state: FSMContext):
    await state.update_data(search_gender=message.text)
    await message.answer("Скільки тобі років?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.age)

@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("З якого ти міста?")
    await state.set_state(Form.city)

@dp.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Надішли своє фото (тільки завантажене, не переслане).")
    await state.set_state(Form.photo)

@dp.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await message.answer("Анкета створена! Бажаємо вдалих знайомств. 😉", reply_markup=main_menu())
    await state.clear()

# --- МІЙ ПРОФІЛЬ (ПАУЗА / ВИДАЛЕННЯ) ---
@dp.message(F.text == "👤 Мій профіль")
async def my_profile(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏸ Поставити на паузу", callback_data="pause_profile")],
        [InlineKeyboardButton(text="♈ Додати Зодіак (опційно)", callback_data="add_zodiac")],
        [InlineKeyboardButton(text="🗑 Видалити анкету", callback_data="delete_profile")]
    ])
    await message.answer("Твій профіль активний ✅\n\nТи можеш тимчасово приховати анкету, щоб тебе не бачили, або видалити її зовсім.", reply_markup=kb)

# --- ПРЕМІУМ ---
@dp.message(F.text == "⭐ Premium")
async def premium_info(message: Message):
    text = (
        "💎 **Твій Premium-конструктор:**\n"
        "— Дивись анкети, коли твоя на паузі\n"
        "— Скасування дизлайка (Я передумав)\n"
        "— Зріст, вага та зодіак у профілі\n"
        "— Анонімний чат\n\n"
        "**Тарифи:**\n"
        "🎫 1 день — 20 грн\n"
        "🎫 1 тиждень — 50 грн\n"
        "🎫 1 місяць — 100 грн\n\n"
        "Будь-яка окрема функція — 20 грн / тиждень."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Активувати безкоштовну годину (раз на тиждень)", callback_data="free_hour")],
        [InlineKeyboardButton(text="Купити Premium", callback_data="buy_premium")]
    ])
    await message.answer(text, reply_markup=kb)

# --- ЛОГІКА СКАРГ (ГЕТЬ) ---
@dp.callback_query(F.data == "report_user_btn") # Викликається з-під анкети
async def report_user_start(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Фейк", callback_data="reason_fake")],
        [InlineKeyboardButton(text="🔞 Пошлість", callback_data="reason_nsfw")],
        [InlineKeyboardButton(text="😤 Образи", callback_data="reason_abuse")],
        [InlineKeyboardButton(text="🚫 Інше", callback_data="reason_other")]
    ])
    await callback.message.answer("Обери причину блокування:", reply_markup=kb)
    await state.set_state(ReportState.choosing_reason)

@dp.callback_query(F.data.startswith("reason_"))
async def report_reason_step(callback: types.CallbackQuery, state: FSMContext):
    reason = callback.data.split("_")[1]
    await state.update_data(current_reason=reason)
    await callback.message.answer("Напиши коротко деталі скарги (або '-', якщо не хочеш писати):")
    await state.set_state(ReportState.waiting_for_details)

@dp.message(ReportState.waiting_for_details)
async def report_final(message: Message, state: FSMContext):
    data = await state.get_data()
    report_text = (
        f"🚨 **НОВА СКАРГА**\n"
        f"👤 Від: {message.from_user.full_name} (ID: `{message.from_user.id}`)\n"
        f"❓ Причина: {data['current_reason']}\n"
        f"📝 Деталі: {message.text}"
    )
    await bot.send_message(chat_id=ADMIN_GROUP_ID, text=report_text)
    await message.answer("Скаргу надіслано. Користувач заблокований. 🙏", reply_markup=main_menu())
    await state.clear()

# --- ЗВ'ЯЗОК З АДМІНОМ ---
@dp.message(F.text == "🆘 Зв'язок з адміном")
async def contact_admin(message: Message):
    await message.answer("Напиши своє питання або пропозицію одним повідомленням. Адмін отримає його в групу підтримки.")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
