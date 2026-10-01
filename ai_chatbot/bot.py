import asyncio
import os
import time
from collections import defaultdict, deque

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from dotenv import load_dotenv

from scripted_chat import PERSONAS, ScriptedChat, run_self_test

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lower().lstrip("@")
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

chat_engine = ScriptedChat()
chat_context = defaultdict(lambda: deque(maxlen=24))
last_bot_reply = defaultdict(float)

SPONTANEOUS_REPLY_PROBABILITY = float(os.getenv("SPONTANEOUS_REPLY_PROBABILITY", "0.12"))
MIN_REPLY_INTERVAL = float(os.getenv("MIN_REPLY_INTERVAL", "20"))

def should_answer(message: Message) -> bool:
    text = message.text or ""
    if not text.strip() or text.startswith("/"):
        return False
    if message.chat.type == "private":
        return True
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_bot:
        return True
    if BOT_USERNAME and f"@{BOT_USERNAME}" in text.lower():
        return True
    if time.monotonic() - last_bot_reply[message.chat.id] < MIN_REPLY_INTERVAL:
        return False
    import random
    return random.random() < SPONTANEOUS_REPLY_PROBABILITY

@dp.message(F.text)
async def on_message(message: Message):
    text = message.text.strip()
    chat_id = message.chat.id
    user_name = message.from_user.full_name if message.from_user else "Пользователь"
    chat_context[chat_id].append(f"{user_name}: {text}")
    if not should_answer(message):
        return
    try:
        persona_name, answer = chat_engine.reply(chat_id, text)
        persona = PERSONAS[persona_name]
        await message.reply(f"{persona['emoji']} {persona_name}: {answer}")
        chat_context[chat_id].append(f"{persona_name}: {answer}")
        last_bot_reply[chat_id] = time.monotonic()
    except Exception as exc:
        print(f"CHAT error: {type(exc).__name__}: {exc}")

async def health(request):
    return web.json_response({"status": "ok", "service": "FREEzzzGames scripted chat"})

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health server listening on port {port}")

async def main():
    print("FREEzzzGames scripted chat starting")
    results = run_self_test()
    print(f"SELF-TEST OK: {len(results)} scenarios")
    await start_health_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
