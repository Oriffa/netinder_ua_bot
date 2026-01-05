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
ADMIN_GROUP_ID = -1001003519981489  # Твоя група для скарг та статистики

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
    reported_user_id = State()
    choosing_reason = State()
    waiting_for_details = State()

# --- ГОЛОВНЕ МЕНЮ ---
def main_menu():
    kb = [
        [KeyboardButton(text="🔍 Дивитись анкети"), KeyboardButton(text="❤️ Мене лайкнули")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="⭐ Premium")],
        [KeyboardButton(text="🆘 Зв'язок з адміном")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ПРИВІТАННЯ ТА ГАРАНТІЯ ПРИВАТНОСТІ ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    welcome_text = (
        "Вітаємо у **Нетіндер** 🖤\n\n"
        "Тут ми цінуємо твій час та безпеку. Будь ласка, поважай своїх співрозмовників — це база нашого ком'юніті.\n\n"
        "🛡 **Про твій номер телефону:**\n"
        "— Він потрібен лише для того, щоб підтвердити, що ти — реальна людина.\n"
        "— **Ми нікому не передаємо твій номер.**\n"
        "— **Ми ніколи не будемо тобі дзвонити.**\n\n"
        "🎁 Твій перший тиждень після реєстрації — **Premium безкоштовно!**"
    )
    await message.answer(
        welcome_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Надати номер 📱", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await state.set_state(Form.phone)

# --- РЕЄСТРАЦІЯ ---
@dp.message(Form.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Дякуємо! Тепер скажи, як тебе звати?", reply_markup=ReplyKeyboardRemove())
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
    await message.answer("Надішли своє фото. Тільки реальні фото, будь ласка.")
    await state.set_state(Form.photo)

@dp.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Сповіщення в адмін-групу
    admin_msg = (
        f"🆕 **Новий користувач!**\n"
        f"👤 {user_data['name']}, {user_data['age']}р., {user_data['city']}\n"
        f"📱 Номер: {user_data['phone']}\n"
        f"🆔 ID: `{message.from_user.id}`"
    )
    await bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_msg)
    
    await message.answer("Анкета створена! Тепер ти можеш дивитись інші анкети. 😉", reply_markup=main_menu())
    await state.clear()

# --- СТАТИСТИКА (ДЛЯ ГРУПИ) ---
@dp.message(Command("stats"), F.chat.id == ADMIN_GROUP_ID)
async def cmd_stats(message: Message):
    await message.answer("📊 **Статистика «Нетіндер»**\n\n👥 Користувачів у базі: 1\n💎 Premium: 1\n📈 Сьогодні: +1")

# --- СКАРГИ (ГЕТЬ) ---
@dp.callback_query(F.data.startswith("reason_"))
async def report_step_2(callback: types.CallbackQuery, state: FSMContext):
    reason = callback.data.split("_")[1]
    await state.update_data(current_reason=reason)
    await callback.message.answer("Опиши коротко, що сталося? (Або надішли '-')")
    await state.set_state(ReportState.waiting_for_details)

@dp.message(ReportState.waiting_for_details)
async def report_step_3(message: Message, state: FSMContext):
    data = await state.get_data()
    report_card = (
        f"🚨 **СКАРГА**\n"
        f"👤 Від: {message.from_user.full_name} (ID: `{message.from_user.id}`)\n"
        f"❓ Причина: {data.get('current_reason')}\n"
        f"📝 Деталі: {message.text}"
    )
    await bot.send_message(chat_id=ADMIN_GROUP_ID, text=report_card)
    await message.answer("Дякуємо, скаргу прийнято. Ми перевіримо анкету порушника. ✅", reply_markup=main_menu())
    await state.clear()

# --- ЗВ'ЯЗОК З АДМІНОМ ---
@dp.message(F.text == "🆘 Зв'язок з адміном")
async def contact_admin(message: Message):
    await message.answer("Напиши своє питання наступним повідомленням. Ми отримаємо його в групі підтримки.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
