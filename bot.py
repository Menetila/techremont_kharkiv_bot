import os
import logging
import requests
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

API_TOKEN = os.getenv("API_TOKEN")
APPSCRIPT_URL = os.getenv("APPSCRIPT_URL")  # URL веб-додатку з Apps Script

if not API_TOKEN or not APPSCRIPT_URL:
    raise ValueError("❌ Не знайдено API_TOKEN або APPSCRIPT_URL")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Стан користувача в пам'яті
user_state = {}

# Кнопки
cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Скасувати")]], resize_keyboard=True)
device_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Телефон"), KeyboardButton(text="💻 Ноутбук")],
        [KeyboardButton(text="🔧 Інше")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message):
    user_state[message.from_user.id] = {"step": "name"}
    await message.answer("👋 Вітаємо у сервісному центрі!\nВведіть своє ім’я:", reply_markup=cancel_kb)

@dp.message(F.text == "❌ Скасувати")
async def cancel(message: types.Message):
    user_state.pop(message.from_user.id, None)
    await message.answer("Скасовано.", reply_markup=ReplyKeyboardRemove())

@dp.message()
async def collect(message: types.Message):
    uid = message.from_user.id
    if uid not in user_state:
        await message.answer("Натисніть /start щоб почати.")
        return

    step = user_state[uid]["step"]

    if step == "name":
        user_state[uid]["name"] = message.text
        user_state[uid]["step"] = "phone"
        await message.answer("📞 Введіть свій номер телефону:")
    elif step == "phone":
        user_state[uid]["phone"] = message.text
        user_state[uid]["step"] = "device"
        await message.answer("🔧 Виберіть пристрій:", reply_markup=device_kb)
    elif step == "device":
        user_state[uid]["device"] = message.text
        user_state[uid]["step"] = "problem"
        await message.answer("Опишіть проблему:", reply_markup=cancel_kb)
    elif step == "problem":
        user_state[uid]["problem"] = message.text

        # надсилаємо у Google Sheets
        try:
            requests.post(APPSCRIPT_URL, json={
                "user_id": uid,
                "name": user_state[uid]["name"],
                "phone": user_state[uid]["phone"],
                "device": user_state[uid]["device"],
                "problem": user_state[uid]["problem"]
                "random": True
            })
            await message.answer("✅ Дякуємо! Заявку прийнято.", reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            logging.error(f"Помилка відправки в Google: {e}")
            await message.answer("⚠ Не вдалося записати заявку. Спробуйте пізніше.")

        user_state.pop(uid, None)

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
