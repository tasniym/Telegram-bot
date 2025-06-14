from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
import os

API_TOKEN = os.getenv("BOT_TOKEN")  # Render.com'da sozlanadi

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Buyurtma tugmalari
start_menu = ReplyKeyboardMarkup(resize_keyboard=True)
start_menu.add(KeyboardButton("📦 Buyurtma berish"))

# Telefonni so‘rash tugmasi
phone_request_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
phone_request_kb.add(KeyboardButton("📱 Raqamni ulashish", request_contact=True))

# Viloyatlar menyusi
regions_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
regions = ["Toshkent", "Andijon", "Farg‘ona", "Namangan", "Buxoro", "Jizzax",
           "Samarqand", "Surxondaryo", "Qashqadaryo", "Navoiy", "Xorazm", "Sirdaryo"]
for r in regions:
    regions_kb.add(KeyboardButton(r))

# /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await msg.answer("📚 Salom! Kitob botiga xush kelibsiz. Quyidagidan tanlang:", reply_markup=start_menu)

# Buyurtma bosilganda
@dp.message_handler(lambda msg: msg.text == "📦 Buyurtma berish")
async def ask_phone(msg: types.Message):
    await msg.answer("Iltimos, telefon raqamingizni ulashing 👇", reply_markup=phone_request_kb)

# Telefon olgach
@dp.message_handler(content_types=['contact'])
async def ask_name(msg: types.Message):
    await msg.answer("Rahmat! Endi ismingiz va familiyangizni yuboring:")

# Ismni qabul qilish
@dp.message_handler(lambda msg: msg.text and msg.text != "📦 Buyurtma berish")
async def ask_region(msg: types.Message):
    if len(msg.text.split()) >= 2:
        await msg.answer("Endi yashash viloyatingizni tanlang:", reply_markup=regions_kb)
    elif msg.text in regions:
        await msg.answer(
            "💳 To‘lov uchun karta raqami: 8600 1234 5678 9012\n"
            "💰 Narxi: 59,000 so‘m\n\n"
            "Iltimos, to‘lovni amalga oshiring va chek (rasm)ni yuboring:"
        )
    elif msg.photo:
        await msg.answer("✅ Chekingiz 24 soat ichida ko‘rib chiqiladi. Rahmat!")
    else:
        await msg.answer("Iltimos, ism va familiyangizni yozing (masalan: Ali Karimov)")

# Chek yuborish
@dp.message_handler(content_types=['photo'])
async def confirm_payment(msg: types.Message):
    await msg.answer("✅ Chekingiz 24 soat ichida ko‘rib chiqiladi. Rahmat!")

