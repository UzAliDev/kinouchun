import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo, FSInputFile
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import asyncio

API_TOKEN = "7554779524:AAFNiA1LUAcYIIri6LTpw85HAimy32khYi4"
CHANNELS = [
    {"id": "-1002268124166", "username": "https://t.me/uzbek_bass_maniya"},  # Kanal 1
    {"id": "-1002406777518", "username": "https://t.me/UzTopFilmlar"},
    {"id": "-1002421755925", "username": "https://t.me/Fastxabarlar"},
    {"id": "-1002306729898", "username": "https://t.me/+kgwjIiPt6UQ3YTZi"}# Kanal 2
]
VIDEO_CHANNEL = -1002007433187  # Videolar joylashgan kanal
ALLOWED_USER_ID = 5557587635 

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()

db = sqlite3.connect("main.db")
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE,
                    first_name TEXT,
                    username TEXT,
                    join_date TEXT)''')
db.commit()

# Keyboard
def get_subscribe_keyboard():
    buttons = [
        [InlineKeyboardButton(text=f"📢 {idx+1}-kanalga qo‘shilish", url=channel["username"])]
        for idx, channel in enumerate(CHANNELS)
    ]
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def add_user(user_id, first_name, username, join_date):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, username, join_date) VALUES (?, ?, ?, ?)",
                   (user_id, first_name, username, join_date))
    db.commit()

async def check_user_subscription(user_id):
    not_subscribed = []
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel["id"], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append(channel["username"])
        except Exception as e:
            logging.error(f"Kanalga obuna tekshirishda xatolik: {e}")
            not_subscribed.append(channel["username"])
    return not_subscribed

@router.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    add_user(user.id, user.first_name, user.username, message.date.strftime("%Y-%m-%d %H:%M:%S"))
    
    not_subscribed = await check_user_subscription(user.id)
    if not_subscribed:
        await message.answer("⛔️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling va tekshirish tugmasini bosing!", reply_markup=get_subscribe_keyboard())
    else:
        await message.answer("✅ Kino IDsini yuboring va sizga mos kino yoki videoni yuboraman!\n\n/start yoki /about")

@router.message(Command("about"))
async def about(message: types.Message):
    await message.answer("Bu bot orqali siz kino IDsiga mos videolarni va kinolarni osongina olishingiz mumkin. Foydalanish uchun kanalga obuna bo‘ling va video IDsini yuboring!\n\n/start yoki /about")

@router.callback_query(lambda c: c.data == 'check')
async def check_subscription(callback_query: types.CallbackQuery):
    user = callback_query.from_user
    not_subscribed = await check_user_subscription(user.id)

    if not_subscribed:
        await callback_query.answer(f"❗Siz hali barcha kanallarga qo‘shilmadingiz! Obuna bo‘ling: {', '.join(not_subscribed)}", show_alert=True)
    else:
        await bot.send_message(user.id, "✅ Kino IDsini yuboring va sizga mos kino yoki videoni yuboraman!")

@router.message(lambda message: message.text.isdigit())
async def send_media(message: types.Message):
    user = message.from_user
    not_subscribed = await check_user_subscription(user.id)

    if not_subscribed:
        await message.answer("⛔️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling va tekshirish tugmasini bosing!", reply_markup=get_subscribe_keyboard())
        return
    
    number = int(message.text)
    try:
        forwarded_message = await bot.copy_message(chat_id=message.chat.id, from_chat_id=VIDEO_CHANNEL, message_id=number)
    except Exception as e:
        await message.answer("❌Kechirasiz, ushbu IDga mos video yoki kino topilmadi.\n\nIltimos, boshqa kino IDsini tekshirib qayta yuboring!.")

@router.message(Command("getdb"))
async def send_db(message: types.Message):
    user_id = message.from_user.id
    if user_id == ALLOWED_USER_ID:
        try:
            db_file = FSInputFile("main.db")
            await message.answer_document(db_file)
        except Exception as e:
            await message.answer(f"❌ Xatolik yuz berdi: {e}")
    else:
        await message.answer("❌ Sizda bu faylni yuklab olishga ruxsat yo‘q.")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
