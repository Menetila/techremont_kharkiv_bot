import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 🔑 Встав сюди свій токен
API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Налаштування логів
logging.basicConfig(level=logging.INFO)

# Ініціалізація
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Словник заявок: {user_id: {"name": ..., "device": ..., "status": ...}}
orders = {}


# 🚀 Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in orders:
        await message.answer("👋 Вітаємо у сервісному центрі!\n"
                             "Напишіть своє ім'я, щоб оформити заявку.")
    else:
        await message.answer("✅ У вас вже є активна заявка.\n"
                             "Очікуйте оновлення статусу.")


# 📝 Отримуємо ім’я
@dp.message(lambda m: m.from_user.id not in orders)
async def get_name(message: types.Message):
    user_id = message.from_user.id
    orders[user_id] = {"name": message.text, "device": None, "status": "Нова"}
    await message.answer("📱 Який пристрій потребує ремонту?")


# 🔧 Отримуємо пристрій
@dp.message(lambda m: orders.get(m.from_user.id) and not orders[m.from_user.id]["device"])
async def get_device(message: types.Message):
    user_id = message.from_user.id
    orders[user_id]["device"] = message.text

    await message.answer(
        f"✅ Заявку прийнято!\n"
        f"Номер: #{user_id}\n"
        f"Клієнт: {orders[user_id]['name']}\n"
        f"Пристрій: {orders[user_id]['device']}\n\n"
        "Очікуйте повідомлення про статус ремонту."
    )


# 🔄 Оновлення статусу (адмін)
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
            await bot.send_message(user_id, f"🔔 Статус вашої заявки оновлено: {new_status}")
            await message.answer("✅ Статус оновлено")
        else:
            await message.answer("❌ Клієнта не знайдено")
    except Exception as e:
        logging.error(f"Помилка у /update: {e}")
        await message.answer("⚠ Сталася помилка. Перевірте команду.")


# 🚀 Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
