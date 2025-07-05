import logging
import os
import asyncio
import threading

from flask import Flask
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# --- TOKEN & ADMIN IDs
API_TOKEN = "7847841979:AAHiQPRZSvqXronN4UlVX37dVel3aOo6fL0"
ADMIN_IDS = [5619056094, 5444347783]

# --- LOGGING
logging.basicConfig(level=logging.INFO)

# --- Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot va Flask birga ishlayapti!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- Aiogram bot setup
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Holatlar (FSM)
class OrderBook(StatesGroup):
    phone = State()
    fullname = State()
    region = State()
    payment = State()

# --- Klaviaturalar
start_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📦 Buyurtma berish"))
restart_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/start"))
phone_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
    KeyboardButton("📱 Raqamni yuborish", request_contact=True))
regions = ["Toshkent", "Andijon", "Farg‘ona", "Namangan", "Buxoro", "Jizzax",
           "Samarqand", "Surxondaryo", "Qashqadaryo", "Navoiy", "Xorazm", "Sirdaryo"]
region_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for r in regions:
    region_kb.add(KeyboardButton(r))

# --- Bot handlers
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("📚 Kitob sotuv bo'lim botiga xush kelibsiz!", reply_markup=start_menu)

@dp.message_handler(lambda msg: msg.text == "📦 Buyurtma berish")
async def ask_phone(message: types.Message):
    await message.answer("📱 Iltimos, telefon raqamingizni ulashing:", reply_markup=phone_kb)
    await OrderBook.phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=OrderBook.phone)
async def receive_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("👤 Ismingiz va familiyangizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await OrderBook.fullname.set()

@dp.message_handler(state=OrderBook.fullname)
async def receive_fullname(message: types.Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    await message.answer("📍 Yashayotgan viloyatingizni tanlang:", reply_markup=region_kb)
    await OrderBook.region.set()

@dp.message_handler(state=OrderBook.region)
async def receive_region(message: types.Message, state: FSMContext):
    if message.text not in regions:
        return await message.answer("❗️ Iltimos, viloyat ro'yxatidan tanlang.")
    await state.update_data(region=message.text)
    await message.answer(
        "💳 To‘lov rekvizitlari:\n\n"
        "<b>Karta:</b> <code>8600 1404 4188 5630</code>\n"
        "<b>Ism:</b> <b>Ulug'bek Mullabayev</b>\n"
        "<b>Narxi:</b> <b>59 000 so‘m</b>\n\n"
        "✅ To‘lovni amalga oshirgach, chekni rasm sifatida yuboring.",
        parse_mode="HTML"
    )
    await OrderBook.payment.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderBook.payment)
async def receive_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    caption = (
        "📥 <b>Yangi buyurtma:</b>\n\n"
        f"📞 <b>Telefon:</b> {data.get('phone')}\n"
        f"👤 <b>Ism:</b> {data.get('fullname')}\n"
        f"📍 <b>Viloyat:</b> {data.get('region')}\n\n"
        f"🧾 <i>Quyida chek rasmi:</i>"
    )
    for admin_id in ADMIN_IDS:
        await bot.send_photo(chat_id=admin_id, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")

    await message.answer(
        "✅ Chekingiz qabul qilindi!\n"
        "⏰ 24 soat ichida ko‘rib chiqiladi va yetkazib beriladi.\n"
        "🛍 Xaridingiz uchun rahmat!\n\n"
        "🔁 Yana buyurtma berish uchun /start tugmasini bosing.",
        reply_markup=restart_menu,
        parse_mode="HTML"
    )
    await state.finish()

@dp.message_handler(state=OrderBook.payment)
async def wrong_payment_format(message: types.Message):
    await message.answer("❌ Iltimos, chekni *rasm* sifatida yuboring.", parse_mode="Markdown")

# --- Bot va Flask ni parallel ishlatish
def start_bot():
    asyncio.run(executor.start_polling(dp, skip_updates=True))

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    start_bot()
