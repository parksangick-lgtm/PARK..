# Telegram Claude Bot

A small Telegram bot that forwards your messages to [Claude](https://www.anthropic.com/claude)
and streams back the replies. It keeps a short per-chat conversation history so
the bot remembers context within a session.

## Features

- Chat with Claude directly in Telegram
- Per-chat conversation memory (in-memory, resets on restart)
- `/reset` to clear history, `/start` and `/help` for usage
- Optional allowlist so only specific Telegram users can use the bot
- Long replies are automatically split to fit Telegram's 4096-character limit

## Setup

1. **Create a bot** with [@BotFather](https://t.me/BotFather) on Telegram and copy the token.
2. **Get an Anthropic API key** from the [Anthropic Console](https://console.anthropic.com/).
3. **Install dependencies** (Python 3.10+):

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure** by copying the example env file and filling it in:

   ```bash
   cp .env.example .env
   # edit .env and set TELEGRAM_BOT_TOKEN and ANTHROPIC_API_KEY
   ```

5. **Run it:**

   ```bash
   python bot.py
   ```

Open Telegram, find your bot, and send it a message.

## Configuration

All settings are read from environment variables (or a local `.env` file):

| Variable             | Required | Default            | Description                                          |
| -------------------- | -------- | ------------------ | ---------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | yes      | —                  | Bot token from @BotFather                            |
| `ANTHROPIC_API_KEY`  | yes      | —                  | Anthropic API key                                    |
| `CLAUDE_MODEL`       | no       | `claude-opus-4-8`  | Model ID to use                                      |
| `MAX_TOKENS`         | no       | `4096`             | Max output tokens per reply                          |
| `SYSTEM_PROMPT`      | no       | (friendly default) | System prompt applied to every conversation          |
| `ALLOWED_USER_IDS`   | no       | (empty = everyone) | Comma-separated Telegram user IDs allowed to chat    |

## Notes

- Conversation history lives in memory and is lost when the process restarts.
  For production, persist it to a database keyed by chat ID.
- The bot uses long polling, so it needs no public URL or webhook setup.
- Adaptive thinking is enabled, letting Claude decide how much to reason per turn.
