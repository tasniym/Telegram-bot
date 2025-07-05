import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.executor import start_webhook
from flask import Flask

# TOKEN & ADMIN IDs
API_TOKEN = os.getenv("7847841979:AAHiQPRZSvqXronN4UlVX37dVel3aOo6fL0")
ADMIN_IDS = [5619056094, 5444347783]

# Logging
logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)

# Aiogram
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Webhook settings
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + WEBHOOK_PATH

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", default=8080))

# FSM states
class OrderBook(StatesGroup):
    phone = State()
    fullname = State()
    region = State()
    payment = State()

# Keyboards
start_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📦 Buyurtma berish"))
restart_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/start"))
phone_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
    KeyboardButton("📱 Raqamni yuborish", request_contact=True))
regions = ["Toshkent", "Andijon", "Farg‘ona", "Namangan", "Buxoro", "Jizzax",
           "Samarqand", "Surxondaryo", "Qashqadaryo", "Navoiy", "Xorazm", "Sirdaryo"]
region_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for r in regions:
    region_kb.add(KeyboardButton(r))

# Filters
SPAM_WORDS = ["1xbet", "aviator", "kazino", "stavka", "https://", "http://", "pul ishlash"]

@dp.message_handler(lambda msg: any(word in msg.text.lower() for word in SPAM_WORDS), content_types=types.ContentType.TEXT)
async def block_spam(message: types.Message):
    await message.reply("🚫 Reklama taqiqlangan!")
    await message.delete()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("📚 Kitob botiga xush kelibsiz!", reply_markup=start_menu)

@dp.message_handler(lambda msg: msg.text == "📦 Buyurtma berish")
async def ask_phone(message: types.Message):
    await message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=phone_kb)
    await OrderBook.phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=OrderBook.phone)
async def receive_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("👤 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await OrderBook.fullname.set()

@dp.message_handler(state=OrderBook.fullname)
async def receive_fullname(message: types.Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    await message.answer("📍 Viloyatingizni tanlang:", reply_markup=region_kb)
    await OrderBook.region.set()

@dp.message_handler(state=OrderBook.region)
async def receive_region(message: types.Message, state: FSMContext):
    if message.text not in regions:
        return await message.answer("❗️ Ro‘yxatdan tanlang.")
    await state.update_data(region=message.text)
    await message.answer(
        "💳 To‘lov ma'lumotlari:\n\n"
        "<b>Karta:</b> <code>8600 1404 4188 5630</code>\n"
        "<b>Ism:</b> Ulug'bek Mullabayev\n"
        "<b>Narx:</b> 59 000 so'm\n\n"
        "✅ To‘lovni amalga oshirgach, chekni yuboring.",
        parse_mode="HTML"
    )
    await OrderBook.payment.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderBook.payment)
async def receive_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    caption = (
        f"📥 Yangi buyurtma:\n\n"
        f"📞 Telefon: {data.get('phone')}\n"
        f"👤 Ism: {data.get('fullname')}\n"
        f"📍 Viloyat: {data.get('region')}\n\n"
        f"🧾 Chek quyida:"
    )
    for admin in ADMIN_IDS:
        await bot.send_photo(chat_id=admin, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
    await message.answer("✅ Chek qabul qilindi. Tez orada bog‘lanamiz.", reply_markup=restart_menu)
    await state.finish()

@dp.message_handler(state=OrderBook.payment)
async def wrong_payment_format(message: types.Message):
    await message.answer("❌ Chekni *rasm* sifatida yuboring.", parse_mode="Markdown")

# Webhook setup
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

# Run webhook
if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
