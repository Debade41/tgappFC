# Telegram Mini App: Колесо фортуны (React + FastAPI)

## Состав
- `miniapp/web` — фронт (React + Vite)
- `miniapp/api` — backend (FastAPI + SQLite)

## Переменные окружения
Backend:
- `BOT_TOKEN`
- `ADMIN_USER_ID`
- `ALLOWED_ORIGINS`

Frontend build:
- `VITE_API_URL`

Bot:
- `WEBAPP_URL`

## Запуск через Docker
```bash
cp miniapp/.env.example miniapp/.env
```

Заполни `miniapp/.env` и запусти:
```bash
cd miniapp
./start.sh
```

## Запуск бота вручную
```bash
BOT_TOKEN=... WEBAPP_URL=... python3 bot.py
```
