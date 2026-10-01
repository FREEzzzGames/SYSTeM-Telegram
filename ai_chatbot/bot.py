import asyncio
import os
from collections import deque

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from dotenv import load_dotenv

from chat_engine import ChatEngine
from scripted_chat import PERSONAS

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
PUBLIC_URL = os.getenv(
    "PUBLIC_URL", "https://freezzzy-ai-chat.onrender.com"
).rstrip("/")
WEBHOOK_PATH = os.getenv(
    "WEBHOOK_PATH", "/telegram/webhook/freezzzzy"
)
WEBHOOK_URL = f"{PUBLIC_URL}{WEBHOOK_PATH}"

GROUP_CHAT_MODE = os.getenv("GROUP_CHAT_MODE", "on").lower() == "on"
DIALOGUE_PROBABILITY = float(os.getenv("DIALOGUE_PROBABILITY", "0.35"))
MAX_DIALOGUE_TURNS = int(os.getenv("MAX_DIALOGUE_TURNS", "2"))
DIALOGUE_DELAY = max(1.0, float(os.getenv("DIALOGUE_DELAY", "2.5")))

bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
engine = ChatEngine(
    dialogue_probability=DIALOGUE_PROBABILITY,
    max_dialogue_turns=MAX_DIALOGUE_TURNS,
)
dialogue_tasks = {}

# Webhook delivery is normally at-least-once. Keep a small in-memory
# idempotency window so a retried Telegram update cannot create duplicate
# persona replies during the same service lifetime.
SEEN_UPDATE_LIMIT = 2000
seen_update_ids = set()
seen_update_order = deque(maxlen=SEEN_UPDATE_LIMIT)


def remember_update(update_id: int) -> bool:
    if update_id in seen_update_ids:
        return False

    if len(seen_update_order) >= SEEN_UPDATE_LIMIT:
        old_id = seen_update_order.popleft()
        seen_update_ids.discard(old_id)

    seen_update_order.append(update_id)
    seen_update_ids.add(update_id)
    return True


def is_user_message(message: Message) -> bool:
    return bool(
        message.text
        and message.text.strip()
        and not message.text.startswith("/")
        and not (message.from_user and message.from_user.is_bot)
    )


def should_answer(message: Message) -> bool:
    if not is_user_message(message):
        return False

    if message.chat.type == "private":
        return True

    if message.chat.type not in ("group", "supergroup"):
        return False

    if not GROUP_CHAT_MODE:
        return bool(
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.is_bot
        )

    return True


def cancel_dialogue(chat_id: int):
    task = dialogue_tasks.pop(chat_id, None)
    if task and not task.done():
        task.cancel()


async def publish_turn(chat_id: int, turn, is_primary=False, reply_to_message=None):
    prefix = f"{PERSONAS[turn.persona]['emoji']} {turn.persona}:"
    if is_primary and reply_to_message is not None:
        sent = await reply_to_message.reply(f"{prefix} {turn.text}")
    else:
        sent = await bot.send_message(chat_id, f"{prefix} {turn.text}")

    print(
        f"CHAT_TURN chat={chat_id} persona={turn.persona} "
        f"kind={'primary' if is_primary else 'internal'} "
        f"message_id={sent.message_id}"
    )


async def run_dialogue(chat_id, turns):
    try:
        for turn in turns:
            await asyncio.sleep(turn.delay)
            await publish_turn(chat_id, turn)
    except asyncio.CancelledError:
        print(f"CHAT_CHAIN_CANCELLED chat={chat_id}")
        raise
    except Exception as exc:
        print(f"CHAT_CHAIN_ERROR type={type(exc).__name__} error={exc}")
    finally:
        current = asyncio.current_task()
        if dialogue_tasks.get(chat_id) is current:
            dialogue_tasks.pop(chat_id, None)


@dp.message(F.text)
async def on_message(message: Message):
    if not should_answer(message):
        return

    chat_id = message.chat.id
    cancel_dialogue(chat_id)

    try:
        turns = engine.user_turn(chat_id, message.text.strip())
        if not turns:
            return

        await publish_turn(
            chat_id,
            turns[0],
            is_primary=True,
            reply_to_message=message,
        )

        remaining = turns[1:]
        if remaining:
            task = asyncio.create_task(run_dialogue(chat_id, remaining))
            dialogue_tasks[chat_id] = task

    except Exception as exc:
        print(f"CHAT_ERROR type={type(exc).__name__} error={exc}")


async def telegram_webhook(request: web.Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != WEBHOOK_SECRET:
        print("WEBHOOK_REJECTED reason=invalid_secret")
        return web.Response(status=403)

    try:
        data = await request.json()
        update_id = data.get("update_id")
        message = data.get("message") or {}
        chat = message.get("chat") or {}
        user = message.get("from") or {}

        print(
            "WEBHOOK_UPDATE "
            f"update_id={update_id} "
            f"chat_id={chat.get('id')} "
            f"chat_type={chat.get('type')} "
            f"user_id={user.get('id')} "
            f"is_bot={user.get('is_bot')} "
            f"has_text={bool(message.get('text'))}"
        )

        if isinstance(update_id, int) and not remember_update(update_id):
            print(f"WEBHOOK_DUPLICATE update_id={update_id}")
            return web.Response(status=200)

        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return web.Response(status=200)
    except Exception as exc:
        print(f"WEBHOOK_ERROR type={type(exc).__name__} error={exc}")
        return web.Response(status=500)


async def health(request: web.Request):
    return web.json_response(
        {
            "status": "ok",
            "service": "FREEzzzGames scripted chat",
            "transport": "telegram_webhook",
            "group_chat_mode": GROUP_CHAT_MODE,
            "dialogue_probability": DIALOGUE_PROBABILITY,
            "max_dialogue_turns": MAX_DIALOGUE_TURNS,
        }
    )


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

    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=["message"],
        drop_pending_updates=False,
    )

    info = await bot.get_webhook_info()
    me = await bot.get_me()

    print(
        "BOT_IDENTITY "
        f"id={me.id} username=@{me.username or '<none>'} "
        f"can_join_groups={me.can_join_groups} "
        f"can_read_all_group_messages={me.can_read_all_group_messages}"
    )
    print(
        "WEBHOOK_READY "
        f"url={info.url or '<empty>'} "
        f"pending={info.pending_update_count} "
        f"last_error_date={info.last_error_date} "
        f"last_error_message={info.last_error_message or '<none>'} "
        f"max_connections={info.max_connections}"
    )
    print(f"CHAT_SERVER_READY port={port}")


async def main():
    print("FREEzzzGames Chat v2 starting")
    result = engine.self_test()
    print(f"CHAT_ENGINE_SELF_TEST OK {result}")
    await start_server()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
