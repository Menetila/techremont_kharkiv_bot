import logging
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # встав сюди токен від BotFather

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Словник для заявок {user_id: {"name": ..., "device": ..., "status": ...}}
orders = {}

# Стартове повідомлення
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("👋 Вітаємо у сервісному центрі!\n"
                        "Напишіть своє ім'я, щоб ми оформили заявку.")

# Отримуємо ім'я
@dp.message_handler(lambda m: message.from_user.id not in orders)
async def get_name(message: types.Message):
    user_id = message.from_user.id
    orders[user_id] = {"name": message.text, "device": None, "status": "Нова"}
    await message.answer("📱 Який пристрій потребує ремонту?")

# Отримуємо тип пристрою
@dp.message_handler(lambda m: orders.get(m.from_user.id) and not orders[m.from_user.id]["device"])
async def get_device(message: types.Message):
    user_id = message.from_user.id
    orders[user_id]["device"] = message.text
    await message.answer(f"✅ Заявку прийнято!\nНомер: #{user_id}\n"
                         f"Клієнт: {orders[user_id]['name']}\n"
                         f"Пристрій: {orders[user_id]['device']}\n\n"
                         "Очікуйте повідомлення про статус ремонту.")

# Команда для адміністратора (оновлення статусу)
@dp.message_handler(commands=["update"])
async def update_status(message: types.Message):
    try:
        args = message.text.split(" ", 2)
        user_id = int(args[1])
        new_status = args[2]

        if user_id in orders:
            orders[user_id]["status"] = new_status
            await bot.send_message(user_id, f"🔔 Статус вашої заявки оновлено: {new_status}")
            await message.answer("✅ Статус оновлено")
        else:
            await message.answer("❌ Клієнта не знайдено")
    except:
        await message.answer("⚠ Використання: /update user_id Новий_статус")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
