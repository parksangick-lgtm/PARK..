"""Quick check that the Anthropic API key works.

Reads ANTHROPIC_API_KEY from the environment or a local .env file.
Run:  python test_api.py
"""

import os
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key or api_key.startswith("sk-ant-...") or api_key == "my_api_key":
    sys.exit(
        "ANTHROPIC_API_KEY is missing or still a placeholder.\n"
        "Put your real key in telegram-claude-bot/.env, e.g.\n"
        "  ANTHROPIC_API_KEY=sk-ant-xxxxx"
    )

client = anthropic.Anthropic(api_key=api_key)

try:
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=200,
        messages=[
            {"role": "user", "content": "Reply with exactly: API key works!"}
        ],
        thinking={"type": "adaptive"},
    )
except anthropic.AuthenticationError:
    sys.exit("❌ Authentication failed — the API key is invalid or revoked.")
except anthropic.PermissionDeniedError as exc:
    sys.exit(f"❌ Permission denied (check billing/credits): {exc}")
except anthropic.APIError as exc:
    sys.exit(f"❌ API error: {exc}")

text = "".join(b.text for b in message.content if b.type == "text")
print("✅ Success! Claude replied:")
print(text)
print(f"\nModel: {message.model} | tokens out: {message.usage.output_tokens}")
