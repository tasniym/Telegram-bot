import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.enums import ParseMode
import asyncio
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789  # O'zingizning Telegram ID

# Log sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Holatlar
class OrderSteps(StatesGroup):
    phone = State()
    fullname = State()
    region = State()
    payment = State()

# Viloyatlar ro'yxati
regions = [
    "Toshkent", "Andijon", "Farg‘ona", "Namangan",
    "Samarqand", "Buxoro", "Xorazm", "Surxondaryo",
    "Qashqadaryo", "Jizzax", "Navoiy", "Sirdaryo"
]

# /start komandasi
@dp.message(F.text == "/start")
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📚 Buyurtma berish")]],
        resize_keyboard=True
    )
    await message.answer("Assalomu alaykum! Kitobni buyurtma berish uchun tugmani bosing 👇", reply_markup=kb)

# Buyurtma berish
@dp.message(F.text == "📚 Buyurtma berish")
async def ask_phone(message: types.Message, state: FSMContext):
    contact_btn = KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)
    kb = ReplyKeyboardMarkup(keyboard=[[contact_btn]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Iltimos, telefon raqamingizni ulashing 👇", reply_markup=kb)
    await state.set_state(OrderSteps.phone)

# Telefonni qabul qilish
@dp.message(OrderSteps.phone, F.contact)
async def ask_name(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Endi to‘liq ismingiz va familiyangizni yozing:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OrderSteps.fullname)

# Ism familiya qabul qilish
@dp.message(OrderSteps.fullname)
async def ask_region(message: types.Message, state: FSMContext):
    await state.update_data(fullname=message.text)

    # 12 viloyat menyusi
    buttons = [[KeyboardButton(text=region)] for region in regions]
    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("Viloyatingizni tanlang:", reply_markup=kb)
    await state.set_state(OrderSteps.region)

# Viloyat tanlash
@dp.message(OrderSteps.region)
async def show_payment_button(message: types.Message, state: FSMContext):
    if message.text not in regions:
        await message.answer("Iltimos, pastdagi ro‘yxatdan viloyatni tanlang.")
        return

    await state.update_data(region=message.text)

    # To‘lov tugmasi
    pay_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="💳 To‘lovni amalga oshirish")]],
        resize_keyboard=True
    )
    await message.answer("Buyurtma tayyor. Davom etish uchun to‘lovni amalga oshiring 👇", reply_markup=pay_kb)
    await state.set_state(OrderSteps.payment)

# To‘lov tugmasini bosganda
@dp.message(OrderSteps.payment, F.text == "💳 To‘lovni amalga oshirish")
async def ask_payment_photo(message: types.Message):
    await message.answer(
        "💳 To‘lov ma’lumotlari:\n\n"
        "📥 Karta raqam: <code>8600 1234 5678 9012</code>\n"
        "💸 Narxi: <b>50 000 so‘m</b>\n\n"
        "✅ Iltimos, to‘lov chekingizni *rasm* qilib yuboring.",
        reply_markup=ReplyKeyboardRemove()
    )

# Chek rasmi
@dp.message(OrderSteps.payment, F.photo)
async def confirm_order(message: types.Message, state: FSMContext):
    data = await state.get_data()

    caption = (
        f"🆕 Yangi buyurtma!\n"
        f"📱 Telefon: {data['phone']}\n"
        f"👤 FIO: {data['fullname']}\n"
        f"📍 Viloyat: {data['region']}\n\n"
        f"🧾 Quyida to‘lov cheki:"
    )

    await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption)
    await message.answer("✅ Chekingiz qabul qilindi. 24 soat ichida tekshirib chiqiladi.")
    await state.clear()

# Rasm emas, boshqa narsa yuborsa
@dp.message(OrderSteps.payment)
async def not_photo(message: types.Message):
    await message.answer("❗ Iltimos, to‘lov chekini *rasm* shaklida yuboring.")

# Botni ishga tushurish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
