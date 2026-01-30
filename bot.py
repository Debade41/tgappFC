import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

if not TOKEN:
    raise SystemExit("BOT_TOKEN is not set")
if not WEBAPP_URL:
    raise SystemExit("WEBAPP_URL is not set")


def kb_start():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Крутить колесо фортуны",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )


bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Добро пожаловать в колесо фортуны", reply_markup=kb_start())


@dp.message()
async def fallback(message: Message):
    await message.answer("Нажми /start")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
