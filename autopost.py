import requests
import os
import random
import sys

print("=== BOT STARTED ===")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

print("Secrets loaded")

if not BOT_TOKEN or not CHAT_ID or not OPENROUTER_API_KEY:
    print("❌ Missing secrets!")
    sys.exit(1)

# ---------- LOAD TOPICS ----------
with open("topics.txt", "r", encoding="utf-8") as f:
    topics = f.read().splitlines()

print("Topics:", topics)

topic = random.choice(topics)
print("Chosen topic:", topic)

# ---------- AI REQUEST ----------
prompt = f"""
Напиши ностальгический пост про {topic}.
Стиль: ламповый, воспоминания 90-х.
Длина: 600-900 символов.
"""

print("Sending request to OpenRouter...")

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "retro-bot"
    },
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    },
    timeout=60
)

print("OpenRouter status:", response.status_code)
print("OpenRouter raw:", response.text)

data = response.json()

# ---------- CHECK AI RESPONSE ----------
if "choices" not in data:
    print("❌ OpenRouter error:", data)
    sys.exit(1)

text = data["choices"][0]["message"]["content"]

print("Generated text OK")

# ---------- SEND TO TELEGRAM ----------
print("Sending message to Telegram...")

tg = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": text
    }
)

print("Telegram status:", tg.status_code)
print("Telegram response:", tg.text)

print("=== DONE ===")
