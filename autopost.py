import requests
import os
import random
import urllib.parse

print("=== RETRO BOT FINAL START ===")

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
RAWG_API_KEY = os.environ["RAWG_API_KEY"]

# ---------------- LOAD GAMES ----------------

with open("topics.txt", encoding="utf-8") as f:
    games = [g.strip() for g in f if g.strip()]

game = random.choice(games)
print("Selected game:", game)

# ---------------- RAWG IMAGE SEARCH ----------------

def get_game_image(game_name):
    query = urllib.parse.quote(game_name)

    url = (
        f"https://api.rawg.io/api/games"
        f"?key={RAWG_API_KEY}"
        f"&search={query}"
        f"&page_size=5"
    )

    r = requests.get(url, timeout=20)
    data = r.json()

    if not data.get("results"):
        return None

    # ищем максимально похожее название
    for g in data["results"]:
        name = g["name"].lower()
        if game_name.lower() in name:
            print("Matched RAWG:", g["name"])
            return g.get("background_image")

    # fallback — первый результат
    return data["results"][0].get("background_image")


image_url = get_game_image(game)

if not image_url:
    raise Exception("No image found — stopping post")

print("Image:", image_url)

# ---------------- GENERATE TEXT ----------------

prompt = f"""
Напиши короткое описание ретро-игры "{game}".

Требования:
- 5–7 предложений
- описание геймплея
- особенности игры
- механики
- без ностальгии
- стиль как обзор игры
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

data = response.json()
text = data["choices"][0]["message"]["content"]

caption = f"<b>{game}</b>\n\n{text}"

# ---------------- SEND TO TELEGRAM ----------------

# ---------------- SEND TO TELEGRAM ----------------

telegram_photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
telegram_text_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

caption = f"<b>{game}</b>\n\n{text}"

MAX_CAPTION = 1024

print("Sending post...")

# ✅ если текст помещается — отправляем одним постом
if len(caption) <= MAX_CAPTION:

    r = requests.post(
        telegram_photo_url,
        data={
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML",
        },
    )

else:
    print("Caption too long — sending as 2 messages")

    # 1️⃣ фото
    r = requests.post(
        telegram_photo_url,
        data={
            "chat_id": CHAT_ID,
            "photo": image_url,
        },
    )

    if not r.json().get("ok"):
        raise Exception("Photo send failed")

    # 2️⃣ текст отдельно
    r = requests.post(
        telegram_text_url,
        data={
            "chat_id": CHAT_ID,
            "text": caption,
            "parse_mode": "HTML",
        },
    )

print("Telegram status:", r.status_code)
print("Telegram response:", r.text)

if not r.json().get("ok"):
    raise Exception("Telegram send failed")

print("=== POST SUCCESS ===")
