import requests
import random
import os

print("=== SEGA AUTO BOT START ===")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

# -------------------------
# LOAD GAMES FROM FILE
# -------------------------

if not os.path.exists("games.txt"):
    raise Exception("games.txt not found")

with open("games.txt", encoding="utf-8") as f:
    games = [g.strip() for g in f.readlines() if g.strip()]

if not games:
    raise Exception("games.txt is empty")

game = random.choice(games)
print("Selected:", game)

# -------------------------
# GET IMAGE FROM RAWG
# -------------------------

def get_image(game):
    url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={game}&page_size=5"
    r = requests.get(url).json()

    for g in r.get("results", []):
        if g.get("background_image"):
            return g["background_image"]

    raise Exception(f"No image found for {game}")

image_url = get_image(game)
print("Image OK")

# -------------------------
# BUILD POST FORMAT
# -------------------------

formats = [

f"""
Напиши короткий пост до 500 символов про игру {game}.
Опиши геймплей и особенности.
Без ностальгии.
В конце задай вопрос.
Добавь теги #sega #retrogaming #megadrive
""",

f"""
Сделай сравнение игры {game} с другой игрой SEGA.
Коротко и по делу.
В конце вопрос аудитории.
Добавь теги #sega #retrogaming
""",

f"""
Напиши интересный факт про игру {game}.
1-2 предложения описания.
Затем вопрос читателю.
Добавь теги.
"""
]

prompt = random.choice(formats)

# -------------------------
# GENERATE TEXT
# -------------------------

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
)

data = response.json()
text = data["choices"][0]["message"]["content"].strip()

# Telegram caption protection
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
    "caption": text,
    "parse_mode": "HTML"
}

r = requests.post(telegram_url, data=payload)

print("Telegram:", r.status_code, r.text)

if not r.ok:
    raise Exception("Telegram send failed")

print("=== POST SUCCESS ===")
