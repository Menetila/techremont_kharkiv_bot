# Telegram Service Center Bot

Цей бот створений для сервісного центру з ремонту техніки.
Він приймає заявки від клієнтів та надсилає повідомлення про статус ремонту.

## 🚀 Деплой на Railway
1. Форкни або завантаж цей репозиторій у GitHub.
2. Зайди на [Railway](https://railway.app/) → New Project → Deploy from GitHub Repo.
3. У Settings → Variables додай:
   - BOT_TOKEN = "токен від BotFather"
4. Railway автоматично встановить залежності та запустить бота.

## 📌 Команди
- `/start` — почати роботу з ботом
- `/update user_id Новий_статус` — оновити статус заявки
