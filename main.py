import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.utils.executor import start_webhook
from flask import Flask

# Load .env
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
admins_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin.strip()) for admin in admins_str.split(",") if admin.strip()]
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

if not API_TOKEN or not WEBHOOK_URL:
    raise ValueError(".env faylda API_TOKEN yoki WEBHOOK_URL topilmadi!")

# Logging
logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)

# Aiogram
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Webhook config
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL_FULL = WEBHOOK_URL + WEBHOOK_PATH
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = PORT

# FSM
class OrderBook(StatesGroup):
    phone = State()
    fullname = State()
    region = State()
    payment = State()

# Keyboards
start_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("\ud83d\udce6 Buyurtma berish"))
restart_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/start"))
phone_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
    KeyboardButton("\ud83d\udcf1 Raqamni yuborish", request_contact=True)
)
regions = ["Toshkent", "Andijon", "Farg\u2018ona", "Namangan", "Buxoro", "Jizzax",
           "Samarqand", "Surxondaryo", "Qashqadaryo", "Navoiy", "Xorazm", "Sirdaryo"]
region_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for r in regions:
    region_kb.add(KeyboardButton(r))

SPAM_WORDS = ["1xbet", "aviator", "kazino", "stavka", "https://", "http://", "pul ishlash"]

@dp.message_handler(lambda msg: any(word in msg.text.lower() for word in SPAM_WORDS), content_types=types.ContentType.TEXT)
async def block_spam(message: types.Message):
    await message.reply("\u26d4\ufe0f Reklama taqiqlangan!")
    await message.delete()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("\ud83d\udcda Kitob botiga xush kelibsiz!", reply_markup=start_menu)

@dp.message_handler(lambda msg: msg.text == "\ud83d\udce6 Buyurtma berish")
async def ask_phone(message: types.Message):
    await message.answer("\ud83d\udcf1 Telefon raqamingizni yuboring:", reply_markup=phone_kb)
    await OrderBook.phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=OrderBook.phone)
async def receive_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number, user_id=message.from_user.id)
    await message.answer("\ud83d\udc64 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await OrderBook.fullname.set()

@dp.message_handler(state=OrderBook.fullname)
async def receive_fullname(message: types.Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    await message.answer("\ud83d\udccd Viloyatingizni tanlang:", reply_markup=region_kb)
    await OrderBook.region.set()

@dp.message_handler(state=OrderBook.region)
async def receive_region(message: types.Message, state: FSMContext):
    if message.text not in regions:
        return await message.answer("\u2757\ufe0f Ro\u2018yxatdan tanlang.")
    await state.update_data(region=message.text)
    await message.answer(
        "\ud83d\udcb3 To\u2018lov ma'lumotlari:\n\n"
        "<b>Karta:</b> <code>8600 1404 4188 5630</code>\n"
        "<b>Ism:</b> Ulug'bek Mullabayev\n"
        "<b>Narx:</b> 59 000 so'm\n\n"
        "\u2705 To\u2018lovni amalga oshirgach, chekni yuboring.",
        parse_mode="HTML"
    )
    await OrderBook.payment.set()

def confirm_buttons(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("\u2705 Tasdiqlansin", callback_data=f"action:confirm:{user_id}"),
            InlineKeyboardButton("\u274c Rad etilsin", callback_data=f"action:reject:{user_id}")
        ]
    ])

@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderBook.payment)
async def receive_payment(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    data = await state.get_data()

    caption = (
        f"\ud83d\udcc5 Yangi buyurtma:\n\n"
        f"\ud83d\udcde Telefon: {data.get('phone')}\n"
        f"\ud83d\udc64 Ism: {data.get('fullname')}\n"
        f"\ud83d\udccd Viloyat: {data.get('region')}\n\n"
        f"\ud83d\udcdf Chek quyida:"
    )
    user_id = data.get('user_id')

    for admin in ADMIN_IDS:
        await bot.send_photo(
            chat_id=admin,
            photo=message.photo[-1].file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=confirm_buttons(user_id=user_id)
        )

    await message.answer("\u2705 Chek qabul qilindi. Tez orada bog\u2018lanamiz.", reply_markup=restart_menu)
    await state.finish()

@dp.message_handler(state=OrderBook.payment)
async def wrong_payment_format(message: types.Message):
    await message.answer("\u274c Chekni *rasm* sifatida yuboring.", parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith("action:"))
async def handle_admin_response(callback_query: CallbackQuery):
    try:
        _, action, user_id_str = callback_query.data.split(":")
        user_id = int(user_id_str)
    except Exception as e:
        await callback_query.answer("\u2757\ufe0f Callback data xato formatda!", show_alert=True)
        return

    if action == "confirm":
        text = "\u2705 Chekingiz muvaffaqiyatli tekshirildi. Tez orada yetkazib beramiz!"
    else:
        text = "\u274c Afsuski, zakazingiz rad etildi. Iltimos, to\u2018lovni to\u2018g\u2018ri amalga oshirganingizga ishonch hosil qiling."

    try:
        await bot.send_message(chat_id=user_id, text=text)
        await callback_query.answer("\u2705 Foydalanuvchiga xabar yuborildi.")
    except Exception as e:
        logging.exception("Foydalanuvchiga yozib bo‘lmadi:")
        await callback_query.answer("\u2757\ufe0f Foydalanuvchiga xabar yuborib bo‘lmadi.", show_alert=True)

# Webhook setup
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL_FULL)

async def on_shutdown(dp):
    await bot.delete_webhook()

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
