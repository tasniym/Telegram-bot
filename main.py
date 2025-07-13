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

# .env yuklash
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN .env faylda topilmadi!")

admins_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin.strip()) for admin in admins_str.split(",") if admin.strip()]

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL .env faylda topilmadi!")

PORT = int(os.getenv("PORT", 8080))

# Flask va aiogram sozlash
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL_FULL = WEBHOOK_URL + WEBHOOK_PATH
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = PORT

# Buyurtma ma'lumotlarini vaqtincha saqlash uchun
user_orders = {}

# Holatlar
class OrderBook(StatesGroup):
    phone = State()
    fullname = State()
    region = State()
    payment = State()

# Klaviaturalar
start_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📦 Buyurtma berish"))
restart_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/start"))
phone_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
    KeyboardButton("📱 Raqamni yuborish", request_contact=True))
regions = ["Toshkent", "Andijon", "Farg‘ona", "Namangan", "Buxoro", "Jizzax",
           "Samarqand", "Surxondaryo", "Qashqadaryo", "Navoiy", "Xorazm", "Sirdaryo"]
region_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for r in regions:
    region_kb.add(KeyboardButton(r))

# SPAM filtr
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
    await state.update_data(phone=message.contact.phone_number, user_id=message.from_user.id)
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

def confirm_buttons(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton("✅ Tasdiqlansin", callback_data=f"action:confirm:{user_id}"),
        InlineKeyboardButton("❌ Rad etilsin", callback_data=f"action:reject:{user_id}")
    ]])

@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderBook.payment)
async def receive_payment(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    data = await state.get_data()

    user_orders[message.from_user.id] = data  # Ma'lumotlarni saqlash

    caption = (
        f"📅 Yangi buyurtma:\n\n"
        f"📞 Telefon: {data.get('phone')}\n"
        f"👤 Ism: {data.get('fullname')}\n"
        f"📍 Viloyat: {data.get('region')}\n\n"
        f"🗾 Chek quyida:"
    )
    user_id = message.from_user.id

    for admin in ADMIN_IDS:
        await bot.send_photo(
            chat_id=admin,
            photo=message.photo[-1].file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=confirm_buttons(user_id=user_id)
        )

    region = data.get("region")
    if region == "Namangan":
        await message.answer(
            "✅ Chekingiz 24 soat ichida adminlarimiz tomonidan tekshirib chiqiladi.\n\n"
            "📦 Buyurtmangiz tekshirib chiqilgandan so'ng Adminlarimizdan biri sizga aloqaga chiqadi keyin zakazingizni O'quv markazimizga kelib olib ketishingiz mumkin bo'ladi.\n\n"
            "🔊 Yana sotib olishni istasangiz pastdagi /start tugmasini bosing.",
            reply_markup=restart_menu
        )
    else:
        await message.answer(
            "✅ To‘lovingiz qabul qilindi. 24 soat ichida adminlarimiz tomonidan tekshirib chiqiladi va 7 ish kuni ichida belgilangan BTS pochtasiga yetkazib beriladi.\n\n"
            "🔊 Yana qayta sotib olishni istasangiz pastdagi /start tugmasini bosing.",
            reply_markup=restart_menu
        )

    await state.finish()

@dp.message_handler(state=OrderBook.payment)
async def wrong_payment_format(message: types.Message):
    await message.answer("❌ Chekni *rasm* sifatida yuboring.", parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith("action:"))
async def handle_admin_response(callback_query: CallbackQuery):
    try:
        _, action, user_id_str = callback_query.data.split(":")
        user_id = int(user_id_str)
    except Exception:
        await callback_query.answer("❗ Callback data xato formatda!", show_alert=True)
        return

    data = user_orders.get(user_id)

    if not data:
        await callback_query.answer("❗ Ma’lumotlar topilmadi!", show_alert=True)
        return

    region = data.get("region", "")

    if action == "confirm":
        await bot.send_message(chat_id=user_id, text="✅ Chekingiz muvaffaqiyatli tekshirildi. Tez orada yetkazib beramiz!")

        if region == "Namangan":
            await bot.send_location(chat_id=user_id, latitude=41.00822673051774, longitude=71.64066054734141)

            photo_path = os.path.join("assets", "vinder_photo.jpg")
            if os.path.exists(photo_path):
                with open(photo_path, "rb") as photo:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=(
                            "🏫 Vinder School\n\n"
                            "📍 O‘quv markaz binosi.\n"
                            "Do‘stlikni asosiy chorraxasidan Promzona tomonga burilganda 1-chi chap tomondagi bino.\n"
                            "⏰ Zakazni olib ketish vaqti: Dushanbadan Jumagacha, 09:00 – 18:00 gacha"
                        )
                    )
            await bot.send_message(chat_id=user_id, text="📞 Biz bilan bog‘lanish: +998 90 797 76 67")

    else:
        await bot.send_message(
            chat_id=user_id,
            text="❌ Afsuski, zakazingiz rad etildi. Iltimos, to‘lovni to‘g‘ri amalga oshirganingizga ishonch hosil qiling."
        )

    await callback_query.answer("✅ Foydalanuvchiga xabar yuborildi.")

# Webhook
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
