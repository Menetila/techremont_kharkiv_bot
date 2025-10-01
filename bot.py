import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = os.getenv("API_TOKEN")
GSHEETS_WEBHOOK = os.getenv("GSHEETS_WEBHOOK")  # URL вебхука з Apps Script

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
orders = {}

# 🚀 /start
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in orders:
        await message.answer("👋 Вітаємо! Напишіть своє ім’я.")
    else:
        await message.answer("✅ У вас вже є заявка.")


# 📝 Отримуємо ім’я
@dp.message(lambda m: m.from_user.id not in orders)
async def get_name(message: types.Message):
    user_id = message.from_user.id
    orders[user_id] = {"name": message.text, "device": None, "status": "Нова"}
    await message.answer("📱 Який пристрій потребує ремонту?")


# 🔧 Отримуємо пристрій та зберігаємо у Google Sheets
@dp.message(lambda m: orders.get(m.from_user.id) and not orders[m.from_user.id]["device"])
async def get_device(message: types.Message):
    user_id = message.from_user.id
    orders[user_id]["device"] = message.text

    # Відправляємо в Google Sheets через Apps Script Webhook
    data = {
        "user_id": user_id,
        "name": orders[user_id]["name"],
        "device": orders[user_id]["device"]
    }
    try:
        requests.post(GSHEETS_WEBHOOK, json=data)
    except Exception as e:
        print("Помилка при відправці в Google Sheets:", e)

    await message.answer(
        f"✅ Заявку прийнято!\n"
        f"Номер: #{user_id}\n"
        f"Клієнт: {orders[user_id]['name']}\n"
        f"Пристрій: {orders[user_id]['device']}\n\n"
        "Очікуйте оновлення статусу."
    )


# 📌 Endpoint для оновлення статусу з Google Sheets
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/send_status")
async def send_status(request: Request):
    data = await request.json()
    user_id = int(data["user_id"])
    status = data["status"]
    await bot.send_message(user_id, f"🔔 Ваш статус оновлено: {status}")
    return {"ok": True}


# 🚀 Запуск
import asyncio

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    uvicorn.run(app, host="0.0.0.0", port=8000)
