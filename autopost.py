import requests
import os
import random
import urllib.parse

print("=== BOT START ===")

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

print("Secrets OK")

# ======================
# LOAD GAMES
# ======================

with open("topics.txt", encoding="utf-8") as f:
    games = [x.strip() for x in f.readlines() if x.strip()]

game = random.choice(games)

print("Selected game:", game)

# ======================
# GET IMAGE
# ======================

def get_image(game):

    base = "https://raw.githubusercontent.com/libretro-thumbnails/Sega - Mega Drive - Genesis/Named_Boxarts/"

    variants = [
        game,
        game.split(" - ")[0],
        game.replace(":", "")
    ]

    for v in variants:
        url = base + urllib.parse.quote(v) + ".png"
        print("Trying image:", url)

        try:
            r = requests.get(url, timeout=15)

            if r.status_code == 200 and len(r.content) > 5000:
                print("Image OK, size:", len(r.content))
                return r.content
        except Exception as e:
            print("Image error:", e)

    print("Fallback image used")
    fallback = "https://upload.wikimedia.org/wikipedia/commons/3/3e/Sega-Genesis-Mk2-6button.jpg"
    return requests.get(fallback).content


image_bytes = get_image(game)

# ======================
# GENERATE TEXT
# ======================

print("Generating text...")

prompt = f"""
Напиши короткое описание игры {game}.
Опиши геймплей, жанр и особенности.
5 предложений.
Стиль — игровой журнал 90-х.
Без ностальгии.
"""

resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    },
    timeout=60
)

print("OpenRouter status:", resp.status_code)
print("OpenRouter raw:", resp.text[:500])

data = resp.json()

text = data["choices"][0]["message"]["content"]

print("Text generated OK")

caption = (text + "\n\n#retro #sega #retrogaming")[:1024]

# ======================
# SEND TO TELEGRAM
# ======================

print("Sending to Telegram...")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

files = {
    "photo": ("game.png", image_bytes)
}

payload = {
    "chat_id": CHAT_ID,
    "caption": caption
}

try:
    r = requests.post(url, data=payload, files=files, timeout=60)

    print("Telegram status:", r.status_code)
    print("Telegram response:", r.text)

except Exception as e:
    print("Telegram ERROR:", e)

print("=== BOT END ===")
