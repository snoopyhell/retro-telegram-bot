import requests
import os
import random
import urllib.parse
import json

print("=== RETRO BOT PRO STARTED ===")

# ======================
# LOAD SECRETS
# ======================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

print("Secrets loaded")

# ======================
# LOAD TOPICS
# ======================

with open("topics.txt", "r", encoding="utf-8") as f:
    topics = [t.strip() for t in f.readlines() if t.strip()]

print("Topics loaded:", len(topics))

# ======================
# ANTI REPEAT SYSTEM
# ======================

USED_FILE = "used_games.json"

if os.path.exists(USED_FILE):
    with open(USED_FILE, "r", encoding="utf-8") as f:
        used_games = json.load(f)
else:
    used_games = []

available_games = [g for g in topics if g not in used_games]

if not available_games:
    print("All games used, resetting history")
    used_games = []
    available_games = topics

topic = random.choice(available_games)

used_games.append(topic)

with open(USED_FILE, "w", encoding="utf-8") as f:
    json.dump(used_games, f)

print("Chosen game:", topic)

# ======================
# GET GAME IMAGE
# ======================

def get_game_image(game_name):

    base_url = (
        "https://raw.githubusercontent.com/"
        "libretro-thumbnails/Sega - Mega Drive - Genesis/"
        "Named_Boxarts/"
    )

    filename = urllib.parse.quote(game_name) + ".png"

    return base_url + filename


image_url = get_game_image(topic)

print("Image URL:", image_url)

# ======================
# GENERATE POST
# ======================

prompt = f"""
Напиши короткий ностальгический пост про игру "{topic}".

Формат:

Название игры

Короткий ностальгический текст 3-5 предложений про атмосферу
ретро-игр 90-х и воспоминания детства.

Стиль:
простая тёплая ностальгия
без эмодзи
без списков
как будто воспоминание игрока 90-х.
"""

print("Generating post...")

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
    },
    timeout=60,
)

print("OpenRouter status:", response.status_code)

data = response.json()

text = data["choices"][0]["message"]["content"]

print("Text generated")

# ======================
# ADD HASHTAGS
# ======================

hashtags = """

#ретро #sega #retrogaming
#90s #segagenesis
"""

post_text = f"{text}\n{hashtags}"

# Telegram caption limit
post_text = post_text[:1024]

# ======================
# SEND PHOTO
# ======================

print("Sending photo...")

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

payload = {
    "chat_id": CHAT_ID,
    "photo": image_url,
    "caption": post_text
}

r = requests.post(telegram_url, data=payload)

print("Telegram status:", r.status_code)

# ======================
# FALLBACK TEXT
# ======================

if r.status_code != 200:

    print("Photo failed, sending text only")

    fallback = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": post_text
        },
    )

    print("Fallback status:", fallback.status_code)

print("=== DONE ===")
