import requests
import os
import random

print("=== BOT START ===")

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

print("Secrets OK")

# ---------- LOAD TOPICS ----------
with open("topics.txt", "r", encoding="utf-8") as f:
    games = f.read().splitlines()

game = random.choice(games)
print("Selected game:", game)

# ---------- IMAGE SEARCH ----------
systems = [
    "Sega - Mega Drive - Genesis",
    "Nintendo - Super Nintendo Entertainment System",
    "Nintendo - Nintendo Entertainment System"
]

def download_image(game):
    safe = game.replace(" ", "%20")

    for system in systems:
        url = f"https://raw.githubusercontent.com/libretro-thumbnails/{system}/Named_Boxarts/{safe}.png"
        print("Trying image:", url)

        try:
            r = requests.get(url, timeout=10)

            if r.status_code == 200 and len(r.content) > 5000:
                with open("cover.png", "wb") as f:
                    f.write(r.content)

                print("Image downloaded OK")
                return True

        except Exception as e:
            print("Image error:", e)

    return False


if not download_image(game):
    print("Using fallback image")
    requests.get(
        "https://upload.wikimedia.org/wikipedia/commons/3/3b/Video-Game-Controller-Icon-IDV-green.svg"
    ).raise_for_status()

# ---------- GENERATE TEXT ----------
prompt = f"""
Напиши короткий пост про игру {game}.

Стиль:
- меньше ностальгии
- больше описания геймплея
- механики игры
- особенности и фишки
- 4-6 предложений
- русский язык
"""

print("Generating text...")

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

print("OpenRouter status:", response.status_code)

data = response.json()
text = data["choices"][0]["message"]["content"]

caption = f"🎮 {game}\n\n{text}"

print("Text generated OK")

# ---------- SEND TO TELEGRAM ----------
print("Sending to Telegram...")

with open("cover.png", "rb") as photo:
    tg = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": caption
        },
        files={
            "photo": photo
        },
        timeout=60
    )

print("Telegram status:", tg.status_code)
print("Telegram response:", tg.text)

print("=== BOT END ===")
