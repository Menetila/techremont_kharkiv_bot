import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from fastapi import FastAPI, Request
import uvicorn
import gspread
from google.oauth2.service_account import Credentials

# --- Конфіг ---
API_TOKEN = os.getenv("API_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")  # ключ як JSON-рядок

if not API_TOKEN or not SPREADSHEET_ID or not GOOGLE_CREDENTIALS_JSON:
    raise ValueError("❌ Не знайдено API_TOKEN або SPREADSHEET_ID або GOOGLE_CREDENTIALS_JSON")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- Підключення до Google Sheets ---
# перетворюємо JSON-рядок у dict
import json
service_account_info = json.loads(GOOGLE_CREDENTIALS_JSON)
credentials = Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID)
orders_ws = sheet.worksheet("Заявки")

# Пам’ять у пам'яті Python
orders = {}

# Кнопки вибору пристрою
device_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Телефон")],
        [KeyboardButton(text="💻 Ноутбук")],
        [KeyboardButton(text="🔧 Інше")]
    ],
    resize_keyboard=True
)

def add_order_to_sheet(user_id, name, device, status):
    """Додає або оновлює рядок у таблиці"""
    # шукаємо user_id у першій колонці
    cell = orders_ws.find(str(user_id))
    if cell:
        # оновлюємо рядок
        row = cell.row
        orders_ws.update(f"B{row}:D{row}", [[name, device, status]])
    else:
        # додаємо новий
        orders_ws.append_row([user_id, name, device, status])

# --- Хендлери бота ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in orders:
        await message.answer(
            "👋 Вітаємо у сервісному центрі!\n"
            "Напишіть своє ім’я, щоб оформити заявку."
        )
    else:
        await message.answer(
            "✅ У вас вже є активна заявка.\nОчікуйте оновлення статусу."
        )

@dp.message(lambda m: m.from_user.id not in orders)
async def get_name(message: types.Message):
    user_id = message.from_user.id
    orders[user_id] = {"name": message.text, "device": None, "status": "Нова"}
    await message.answer("📱 Який пристрій потребує ремонту?", reply_markup=device_keyboard)

@dp.message(lambda m: orders.get(m.from_user.id) and not orders[m.from_user.id]["device"])
async def get_device(message: types.Message):
    user_id = message.from_user.id
    orders[user_id]["device"] = message.text
    orders[user_id]["status"] = "Нова"
    # пишемо в Sheets
    add_order_to_sheet(user_id, orders[user_id]['name'], orders[user_id]['device'], orders[user_id]['status'])
    await message.answer(
        f"✅ Заявку прийнято!\n"
        f"Номер: #{user_id}\n"
        f"Клієнт: {orders[user_id]['name']}\n"
        f"Пристрій: {orders[user_id]['device']}\n\n"
        "Очікуйте повідомлення про статус ремонту.",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(Command("update"))
async def update_status(message: types.Message):
    try:
        args = message.text.split(" ", 2)
        if len(args) < 3:
            await message.answer("⚠ Використання: /update user_id Новий_статус")
            return

        user_id = int(args[1])
        new_status = args[2]

        if user_id in orders:
            orders[user_id]["status"] = new_status
            add_order_to_sheet(user_id, orders[user_id]['name'], orders[user_id]['device'], new_status)
            await bot.send_message(user_id, f"🔔 Статус вашої заявки оновлено: {new_status}")
            await message.answer("✅ Статус оновлено")
        else:
            await message.answer("❌ Клієнта не знайдено")
    except Exception as e:
        logging.error(f"Помилка у /update: {e}")
        await message.answer("⚠ Сталася помилка. Перевірте команду.")

# --- Ендпоінт FastAPI (опціонально) ---
@app.post("/send_status")
async def send_status(request: Request):
    data = await request.json()
    uid = int(data["user_id"])
    status = data["status"]
    if uid not in orders:
        orders[uid] = {"name": "Невідомо", "device": "?", "status": status}
    orders[uid]["status"] = status
    add_order_to_sheet(uid, orders[uid]['name'], orders[uid]['device'], status)
    await bot.send_message(uid, f"🔔 Статус вашої заявки оновлено: {status}")
    return {"ok": True}

# --- Запуск ---
async def run_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(run_bot())
    uvicorn.run(app, host="0.0.0.0", port=8000)
