import asyncio
import os
import time
from collections import defaultdict, deque

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from dotenv import load_dotenv

from scripted_chat import PERSONAS, ScriptedChat, run_self_test, run_dialogue_self_test

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lower().lstrip("@")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://freezzzy-ai-chat.onrender.com").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook/freezzzzy")
WEBHOOK_URL = f"{PUBLIC_URL}{WEBHOOK_PATH}"

bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

chat_engine = ScriptedChat()
chat_context = defaultdict(lambda: deque(maxlen=24))
last_bot_reply = defaultdict(float)
dialogue_tasks = {}

SPONTANEOUS_REPLY_PROBABILITY = float(os.getenv("SPONTANEOUS_REPLY_PROBABILITY", "0.35"))
GROUP_CHAT_MODE = os.getenv("GROUP_CHAT_MODE", "on").lower() == "on"
MIN_REPLY_INTERVAL = float(os.getenv("MIN_REPLY_INTERVAL", "20"))
DIALOGUE_TURNS = max(0, min(3, int(os.getenv("DIALOGUE_TURNS", "3"))))
DIALOGUE_DELAY = max(1.0, float(os.getenv("DIALOGUE_DELAY", "2.5")))

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
    if GROUP_CHAT_MODE and message.chat.type in ("group", "supergroup"):
        if time.monotonic() - last_bot_reply[message.chat.id] < MIN_REPLY_INTERVAL:
            return False
        return True
    if time.monotonic() - last_bot_reply[message.chat.id] < MIN_REPLY_INTERVAL:
        return False
    import random
    return random.random() < SPONTANEOUS_REPLY_PROBABILITY

async def continue_dialogue(chat_id, previous_persona, previous_text):
    try:
        for step in range(1, DIALOGUE_TURNS + 1):
            await asyncio.sleep(DIALOGUE_DELAY)
            persona_name, answer = chat_engine.dialogue_reply(
                chat_id, previous_persona, previous_text, step
            )
            persona = PERSONAS[persona_name]
            sent = await bot.send_message(
                chat_id,
                f"{persona['emoji']} {persona_name}: {answer}",
            )
            chat_context[chat_id].append(f"{persona_name}: {answer}")
            previous_persona = persona_name
            previous_text = answer
            last_bot_reply[chat_id] = time.monotonic()
            print(
                f"DIALOGUE chat={chat_id} step={step} "
                f"persona={persona_name} message_id={sent.message_id}"
            )
    except asyncio.CancelledError:
        print(f"DIALOGUE cancelled chat={chat_id}")
        raise
    except Exception as exc:
        print(f"DIALOGUE error: {type(exc).__name__}: {exc}")
    finally:
        current = asyncio.current_task()
        if dialogue_tasks.get(chat_id) is current:
            dialogue_tasks.pop(chat_id, None)

def start_dialogue(chat_id, persona_name, answer):
    previous = dialogue_tasks.get(chat_id)
    if previous and not previous.done():
        previous.cancel()
    if DIALOGUE_TURNS > 0:
        dialogue_tasks[chat_id] = asyncio.create_task(
            continue_dialogue(chat_id, persona_name, answer)
        )

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
        sent = await message.reply(f"{persona['emoji']} {persona_name}: {answer}")
        chat_context[chat_id].append(f"{persona_name}: {answer}")
        last_bot_reply[chat_id] = time.monotonic()
        print(
            f"USER_REPLY chat={chat_id} persona={persona_name} "
            f"message_id={sent.message_id}"
        )
        start_dialogue(chat_id, persona_name, answer)
    except Exception as exc:
        print(f"CHAT error: {type(exc).__name__}: {exc}")

async def telegram_webhook(request: web.Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return web.Response(status=200)
    except Exception as exc:
        print(f"WEBHOOK error: {type(exc).__name__}: {exc}")
        return web.Response(status=500)

async def health(request):
    return web.json_response({
        "status": "ok",
        "service": "FREEzzzGames scripted chat",
        "transport": "telegram_webhook",
        "dialogue_turns": DIALOGUE_TURNS,
        "group_chat_mode": GROUP_CHAT_MODE,
    })

async def start_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_post(WEBHOOK_PATH, telegram_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    allowed_updates = dp.resolve_used_update_types()
    await bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=allowed_updates,
        drop_pending_updates=False,
    )

    info = await bot.get_webhook_info()
    print(
        f"Telegram webhook configured: url={info.url or '<empty>'} "
        f"pending={info.pending_update_count}"
    )
    print(f"Health/webhook server listening on port {port}")

async def main():
    print("FREEzzzGames scripted chat starting")
    results = run_self_test()
    print(f"SELF-TEST OK: {len(results)} scenarios")
    dialogue = run_dialogue_self_test()
    print(f"DIALOGUE-SELF-TEST OK: {dialogue}")
    await start_server()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
