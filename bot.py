from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
import os

API_TOKEN = os.getenv("BOT_TOKEN")
admin_chat_id = 123456789  # <-- Bu yerga admin Telegram ID ni yozing

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

start_menu = ReplyKeyboardMarkup(resize_keyboard=True)
start_menu.add(KeyboardButton("📦 Buyurtma berish"))

phone_request_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
phone_request_kb.add(KeyboardButton("📱 Raqamni ulashish", request_contact=True))

regions_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
regions = ["Toshkent", "Andijon", "Farg‘ona", "Namangan", "Buxoro", "Jizzax",
           "Samarqand", "Surxondaryo", "Qashqadaryo", "Navoiy", "Xorazm", "Sirdaryo"]
for r in regions:
    regions_kb.add(KeyboardButton(r))

# Global foydalanuvchi ma'lumotlarini saqlash uchun
user_data = {}

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await msg.answer("📚 Salom! Kitob botiga xush kelibsiz. Quyidagidan tanlang:", reply_markup=start_menu)

@dp.message_handler(lambda msg: msg.text == "📦 Buyurtma berish")
async def ask_phone(msg: types.Message):
    user_data[msg.from_user.id] = {}
    await msg.answer("Iltimos, telefon raqamingizni ulashing 👇", reply_markup=phone_request_kb)

@dp.message_handler(content_types=['contact'])
async def ask_name(msg: types.Message):
    user_data[msg.from_user.id]['phone'] = msg.contact.phone_number
    await msg.answer("Rahmat! Endi ismingiz va familiyangizni yozing:")

@dp.message_handler(lambda msg: msg.text in regions)
async def ask_payment(msg: types.Message):
    user_data[msg.from_user.id]['region'] = msg.text
    await msg.answer(
        "💳 To‘lov uchun karta raqami: 8600 1234 5678 9012\n"
        "💰 Narxi: 59,000 so‘m\n\n"
        "Iltimos, to‘lovni amalga oshiring va chek (rasm)ni yuboring:"
    )

@dp.message_handler(lambda msg: msg.text and 'phone' in user_data.get(msg.from_user.id, {}))
async def get_region(msg: types.Message):
    user_data[msg.from_user.id]['name'] = msg.text
    await msg.answer("Endi yashash viloyatingizni tanlang:", reply_markup=regions_kb)

@dp.message_handler(content_types=['photo'])
async def confirm_payment(msg: types.Message):
    await msg.answer("✅ Chekingiz 24 soat ichida ko‘rib chiqiladi. Rahmat!")

    data = user_data.get(msg.from_user.id, {})
    caption = (
        "🆕 Yangi buyurtma!\n\n"
        f"👤 Ism: {data.get('name', 'Noma’lum')}\n"
        f"📞 Telefon: {data.get('phone', 'Noma’lum')}\n"
        f"📍 Viloyat: {data.get('region', 'Noma’lum')}\n"
        f"📸 Quyida to‘lov cheki ilova qilingan."
    )

    photo = msg.photo[-1].file_id
    await bot.send_photo(admin_chat_id, photo=photo, caption=caption)

