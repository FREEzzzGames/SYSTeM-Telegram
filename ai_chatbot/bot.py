import asyncio
import os
import random
import time
from collections import defaultdict, deque

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI

from personas import PERSONAS, SYSTEM_RULES

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "256"))

bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
ai = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

chat_context = defaultdict(lambda: deque(maxlen=24))
last_bot_reply = defaultdict(float)

SPONTANEOUS_REPLY_PROBABILITY = float(
    os.getenv("SPONTANEOUS_REPLY_PROBABILITY", "0.12")
)
MIN_REPLY_INTERVAL = float(os.getenv("MIN_REPLY_INTERVAL", "20"))


def choose_persona(text: str) -> str:
    t = text.lower()

    if any(x in t for x in ("игр", "game", "steam", "android", "код", "программ")):
        return "zadr0t"
    if any(x in t for x in ("стрим", "live", "youtube", "ютуб", "канал")):
        return "mamkinBlogger"
    if any(x in t for x in ("шут", "мем", "скуч", "виктор", "😂")):
        return "tipoFUN"

    return random.choice(["FREEzzzy", "RakNaDne", "tipoFUN"])


def should_answer(message: Message) -> bool:
    text = message.text or ""
    if not text.strip():
        return False

    # In a private chat the user is explicitly talking to the bot.
    if message.chat.type == "private":
        return not text.startswith("/")

    if text.startswith("/"):
        return False

    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.is_bot:
            return True

    bot_username = os.getenv("BOT_USERNAME", "").lower()
    if bot_username and f"@{bot_username}" in text.lower():
        return True

    chat_id = message.chat.id
    if time.monotonic() - last_bot_reply[chat_id] < MIN_REPLY_INTERVAL:
        return False

    return random.random() < SPONTANEOUS_REPLY_PROBABILITY


async def generate_reply(chat_id: int, user_name: str, text: str):
    persona_name = choose_persona(text)
    persona = PERSONAS[persona_name]
    history = "\n".join(chat_context[chat_id])

    prompt = f"""
Персонаж: {persona_name} {persona["emoji"]}
Роль: {persona["role"]}
Манера: {persona["style"]}

Контекст последних сообщений:
{history}

Пользователь {user_name} написал:
{text}

Ответь естественно. Обычно 1–3 коротких предложения.
"""

    response = await ai.responses.create(
        model=DEEPSEEK_MODEL,
        instructions=SYSTEM_RULES,
        input=prompt,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )

    usage = getattr(response, "usage", None)
    if usage:
        print(
            "DeepSeek usage: "
            f"input={getattr(usage, 'input_tokens', 0)}, "
            f"output={getattr(usage, 'output_tokens', 0)}, "
            f"total={getattr(usage, 'total_tokens', 0)}"
        )

    return persona_name, response.output_text.strip()


@dp.message(F.text)
async def on_message(message: Message):
    text = message.text.strip()
    chat_id = message.chat.id
    user_name = message.from_user.full_name if message.from_user else "Пользователь"

    chat_context[chat_id].append(f"{user_name}: {text}")

    if not should_answer(message):
        return

    try:
        persona_name, answer = await generate_reply(chat_id, user_name, text)
        if not answer:
            return

        answer = answer[:3500]
        persona = PERSONAS[persona_name]

        await message.reply(f"{persona['emoji']} {persona_name}: {answer}")

        chat_context[chat_id].append(f"{persona_name}: {answer}")
        last_bot_reply[chat_id] = time.monotonic()

    except Exception as exc:
        print(f"AI error: {type(exc).__name__}: {exc}")


async def health(request):
    return web.json_response({"status": "ok", "service": "FREEzzzGames AI"})


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
    print("FREEzzzGames AI Telegram bot started")
    await start_health_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
