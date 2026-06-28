"""A Telegram bot powered by Claude.

Run with:  python bot.py

Configuration is read from environment variables (see .env.example). A local
.env file is loaded automatically if present.
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict, deque

import anthropic
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# python-telegram-bot is chatty at INFO; keep its HTTP logs quieter.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("telegram-claude-bot")

# --- Configuration -----------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))
SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    "You are a helpful assistant chatting with users over Telegram. "
    "Keep replies concise and friendly.",
)


def _parse_allowed_ids(raw: str | None) -> set[int]:
    if not raw:
        return set()
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part:
            ids.add(int(part))
    return ids


ALLOWED_USER_IDS = _parse_allowed_ids(os.environ.get("ALLOWED_USER_IDS"))

# Keep the last N turns (user + assistant messages) per chat in memory.
MAX_HISTORY_MESSAGES = 20
# Telegram rejects messages longer than 4096 characters.
TELEGRAM_MAX_MESSAGE_LEN = 4096

# In-memory conversation history keyed by chat id. Resets when the bot restarts.
_histories: dict[int, deque[dict[str, str]]] = defaultdict(
    lambda: deque(maxlen=MAX_HISTORY_MESSAGES)
)

claude = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


# --- Helpers -----------------------------------------------------------------


def _is_allowed(update: Update) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    user = update.effective_user
    return user is not None and user.id in ALLOWED_USER_IDS


def _split_message(text: str, limit: int = TELEGRAM_MAX_MESSAGE_LEN) -> list[str]:
    """Split a long reply into Telegram-sized chunks, preferring line breaks."""
    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit)
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip("\n")
    if remaining:
        chunks.append(remaining)
    return chunks


async def _ask_claude(history: deque[dict[str, str]]) -> str:
    """Send the conversation to Claude and return the assistant's text reply."""
    # Stream so that large max_tokens responses don't hit request timeouts.
    async with claude.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        messages=list(history),
    ) as stream:
        message = await stream.get_final_message()

    parts = [block.text for block in message.content if block.type == "text"]
    return "\n".join(parts).strip() or "(Claude returned an empty response.)"


# --- Handlers ----------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return
    await update.message.reply_text(
        "👋 Hi! I'm a Claude-powered bot. Just send me a message and I'll reply.\n\n"
        "Commands:\n"
        "/reset - clear our conversation history\n"
        "/help - show this message"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    _histories.pop(update.effective_chat.id, None)
    await update.message.reply_text("🧹 Conversation history cleared.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    history = _histories[chat_id]
    history.append({"role": "user", "content": user_text})

    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

    try:
        reply = await _ask_claude(history)
    except anthropic.APIError as exc:
        logger.exception("Anthropic API error")
        # Drop the user turn we couldn't answer so history stays consistent.
        if history and history[-1]["role"] == "user":
            history.pop()
        await update.message.reply_text(f"⚠️ Claude API error: {exc}")
        return

    history.append({"role": "assistant", "content": reply})

    for chunk in _split_message(reply):
        await update.message.reply_text(chunk)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception", exc_info=context.error)


# --- Entry point -------------------------------------------------------------


def main() -> None:
    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
            ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
        )
        if not value
    ]
    if missing:
        raise SystemExit(
            "Missing required environment variables: "
            + ", ".join(missing)
            + "\nCopy .env.example to .env and fill in the values."
        )

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(on_error)

    logger.info("Starting bot with model %s", CLAUDE_MODEL)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
