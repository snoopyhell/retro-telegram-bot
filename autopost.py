import requests
import random
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
RAWG_API_KEY = os.environ["RAWG_API_KEY"]

print("=== RETRO BOT AUTO START ===")

# ---------------- LOAD GAME ----------------

with open("games.txt", encoding="utf-8") as f:
    games = [g.strip() for g in f if g.strip()]

game = random.choice(games)
print("Selected:", game)

# ---------------- GET IMAGE FROM RAWG ----------------

def get_game_image(name):

    url = "https://api.rawg.io/api/games"

    r = requests.get(
        url,
        params={
            "key": RAWG_API_KEY,
            "search": name,
            "page_size": 1
        },
        timeout=30
    )

    data = r.json()

    results = data.get("results")

    if not results:
        return None

    image = results[0].get("background_image")

    return image


image_url = get_game_image(game)

print("Image:", image_url)

# ---------------- GENERATE TEXT ----------------

def generate_text(game):

    prompt = f"""
Опиши ретро-игру {game}.
Кратко расскажи:
- геймплей
- механики
- особенности
4 предложения.
Без ностальгии.
"""

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=120
    )

    r.raise_for_status()

    return r.json()["choices"][0]["message"]["content"].strip()


text = generate_text(game)

caption = f"🎮 {game}\n\n{text}"

# ---------------- TELEGRAM POST ----------------

if image_url:

    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": caption[:1024]
        },
        timeout=60
    )

else:

    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": caption
        }
    )

print("Telegram:", r.text)
r.raise_for_status()

print("=== POST SUCCESS ===")
