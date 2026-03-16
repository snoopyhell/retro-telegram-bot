import requests
import os
import random
import urllib.parse

print("=== BOT START ===")

# =============================
# SECRETS
# =============================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

print("Secrets OK")

# =============================
# LOAD TOPICS
# =============================
with open("topics.txt", "r", encoding="utf-8") as f:
    games = [g.strip() for g in f.readlines() if g.strip()]

game = random.choice(games)
print("Selected game:", game)

# =============================
# IMAGE SETTINGS
# =============================
IMAGE_PATH = "cover.png"
FALLBACK_IMAGE = "fallback.png"

SYSTEMS = [
    "Sega - Mega Drive - Genesis",
    "Nintendo - Super Nintendo Entertainment System",
    "Nintendo - Nintendo Entertainment System",
    "Sony - PlayStation",
    "Nintendo - Game Boy Advance",
]

BASE_URL = "https://raw.githubusercontent.com/libretro-thumbnails"


# =============================
# DOWNLOAD IMAGE
# =============================
def download_image(game_name):
    encoded = urllib.parse.quote(game_name)

    for system in SYSTEMS:
        url = f"{BASE_URL}/{system}/Named_Boxarts/{encoded}.png"

        print("Trying image:", url)

        try:
            r = requests.get(url, timeout=15)

            if r.status_code == 200 and len(r.content) > 5000:
                with open(IMAGE_PATH, "wb") as f:
                    f.write(r.content)

                print("Image downloaded OK")
                return True

        except Exception as e:
            print("Image error:", e)

    return False


# =============================
# IMAGE SELECT
# =============================
if not download_image(game):
    print("Using local fallback image")
    IMAGE_PATH = FALLBACK_IMAGE

print("Image size:", os.path.getsize(IMAGE_PATH))


# =============================
# GENERATE TEXT (GAMEPLAY STYLE)
# =============================
print("Generating text...")

prompt = f"""
Напиши короткий пост (3-5 предложений) про игру {game}.

Стиль:
- описание геймплея
- особенности игры
- механики
- чем игра выделялась
- без сильной ностальгии
- живой игровой стиль

Без эмодзи.
"""

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    },
    timeout=60,
)

print("OpenRouter status:", response.status_code)
print("OpenRouter raw:", response.text[:300])

data = response.json()

text = data["choices"][0]["message"]["content"].strip()

caption = f"🎮 {game}\n\n{text}"

print("Text generated OK")


# =============================
# SEND TO TELEGRAM
# =============================
print("Sending to Telegram...")

with open(IMAGE_PATH, "rb") as photo:
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
        },
        files={"photo": photo},
        timeout=60,
    )

print("Telegram status:", r.status_code)
print("Telegram response:", r.text)

print("=== BOT END ===")
