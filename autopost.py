import requests
import random
import os
import time

print("=== SEGA AUTO BOT START ===")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

# -------------------------
# LOAD GAMES
# -------------------------

if not os.path.exists("games.txt"):
    raise Exception("games.txt not found")

with open("games.txt", encoding="utf-8") as f:
    games = [g.strip() for g in f.readlines() if g.strip()]

if not games:
    raise Exception("games.txt empty")

# -------------------------
# SAFE RAWG REQUEST
# -------------------------

def safe_json_request(url):
    try:
        r = requests.get(url, timeout=15)

        if r.status_code != 200:
            print("RAWG bad status:", r.status_code)
            return None

        if not r.text.strip():
            print("RAWG empty response")
            return None

        return r.json()

    except Exception as e:
        print("RAWG request error:", e)
        return None


# -------------------------
# FIND IMAGE (RETRY LOGIC)
# -------------------------

def get_image(game):

    search_variants = [
        game,
        game.split(":")[0],
        game.replace("-", " "),
    ]

    for name in search_variants:

        url = (
            f"https://api.rawg.io/api/games"
            f"?key={RAWG_API_KEY}"
            f"&search={name}"
            f"&page_size=5"
        )

        data = safe_json_request(url)

        if not data:
            continue

        for g in data.get("results", []):
            img = g.get("background_image")
            if img:
                print("Matched RAWG:", g["name"])
                return img

    return None


# -------------------------
# TRY MULTIPLE GAMES
# -------------------------

image_url = None
game = None

random.shuffle(games)

for candidate in games[:10]:  # try 10 games max
    print("Trying:", candidate)

    img = get_image(candidate)

    if img:
        game = candidate
        image_url = img
        break

if not image_url:
    raise Exception("No valid image found after retries")

print("Selected:", game)
print("Image OK")

# -------------------------
# PROMPT TYPES
# -------------------------

prompts = [

f"""Опиши геймплей игры {game}.
Кратко, информативно, без ностальгии.
До 450 символов.
В конце вопрос читателю.
Добавь теги #sega #retrogaming #megadrive""",

f"""Сравни игру {game} с другой игрой SEGA.
Коротко и по делу.
Добавь вопрос аудитории и теги.""",

f"""Расскажи интересную особенность игры {game}.
Без воды.
До 400 символов.
Добавь теги."""
]

prompt = random.choice(prompts)

# -------------------------
# GENERATE TEXT
# -------------------------

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    },
    timeout=30
)

data = resp.json()
text = data["choices"][0]["message"]["content"].strip()

# Telegram caption limit safety
if len(text) > 900:
    text = text[:880] + "..."

print("Text generated")

# -------------------------
# SEND TO TELEGRAM
# -------------------------

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

payload = {
    "chat_id": CHAT_ID,
    "photo": image_url,
    "caption": text
}

r = requests.post(telegram_url, data=payload)

print("Telegram:", r.status_code, r.text)

if not r.ok:
    raise Exception("Telegram send failed")

print("=== POST SUCCESS ===")
