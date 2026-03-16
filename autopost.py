import requests
import os
import random
import urllib.parse
import json

print("=== RETRO BOT ULTRA FINAL ===")

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

# ======================
# LOAD GAMES
# ======================

with open("topics.txt", "r", encoding="utf-8") as f:
    games = [x.strip() for x in f.readlines() if x.strip()]

game = random.choice(games)

print("Game:", game)

# ======================
# IMAGE SEARCH
# ======================

def find_image(game):

    base = "https://raw.githubusercontent.com/libretro-thumbnails/Sega - Mega Drive - Genesis/Named_Boxarts/"

    variants = [
        game,
        game.split(" - ")[0],
        game.replace(":", ""),
    ]

    for v in variants:
        name = urllib.parse.quote(v) + ".png"
        url = base + name

        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and len(r.content) > 10000:
                print("Image found:", url)
                return r.content
        except:
            pass

    print("Using fallback image")

    fallback = "https://upload.wikimedia.org/wikipedia/commons/3/3e/Sega-Genesis-Mk2-6button.jpg"
    return requests.get(fallback).content


image_bytes = find_image(game)

# ======================
# AI POST (GAMEPLAY STYLE)
# ======================

prompt = f"""
Напиши короткий пост про игру {game}.

Стиль:
— описание геймплея
— особенности игры
— чем она отличалась
— атмосфера 90-х

НЕ ностальгический рассказ.
НЕ воспоминания.
Пиши как обзор из игрового журнала.

5–6 коротких предложений.
Без эмодзи.
"""

response = requests.post(
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

data = response.json()

text = data["choices"][0]["message"]["content"]

hashtags = """

#retro #retrogaming #sega #segagenesis
"""

caption = (text + hashtags)[:1024]

print("Post ready")

# ======================
# SEND PHOTO (REAL UPLOAD)
# ======================

send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

files = {
    "photo": ("game.png", image_bytes)
}

data = {
    "chat_id": CHAT_ID,
    "caption": caption
}

r = requests.post(send_url, data=data, files=files)

print("Telegram:", r.status_code)
print(r.text)

print("=== DONE ===")
