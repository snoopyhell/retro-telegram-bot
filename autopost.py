import requests
import os
import random
import urllib.parse
import json

print("=== RETRO BOT ULTRA STARTED ===")

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

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

available = [g for g in topics if g not in used_games]

if not available:
    used_games = []
    available = topics

game = random.choice(available)
used_games.append(game)

with open(USED_FILE, "w", encoding="utf-8") as f:
    json.dump(used_games, f)

print("Chosen game:", game)

# ======================
# IMAGE SYSTEM (ИСПРАВЛЕНО)
# ======================

def get_game_image(game):
    # Исправленный путь к мастер-ветке репозитория
    base = "https://raw.githubusercontent.com"
    
    # Очистка названия: заменяем двоеточие на подчеркивание (стандарт libretro)
    clean_name = game.replace(":", " _")
    name1 = urllib.parse.quote(clean_name) + ".png"
    url1 = base + name1

    # Проверяем, существует ли такая картинка
    try:
        r = requests.head(url1, timeout=10)
        if r.status_code == 200:
            return url1
    except:
        pass

    # Запасной вариант (если первая ссылка битая)
    return "https://upload.wikimedia.org"


image_url = get_game_image(game)
print("Image selected:", image_url)

# ======================
# GENERATE POST
# ======================

prompt = f"""
Напиши короткий ностальгический пост про игру {game}.
Формат: Название игры, 3-4 предложения воспоминаний.
Стиль: тёплая ностальгия, без эмодзи.
"""

print("Generating post...")

response = requests.post(
    "https://openrouter.ai",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    },
    timeout=60
)

data = response.json()
# Важно: здесь должен быть индекс [0]
text = data["choices"][0]["message"]["content"]

# ======================
# HASHTAGS
# ======================

hashtags = "\n\n#retro #sega #90s #videogames"
post = f"{text}{hashtags}"[:1024]

# ======================
# SEND TO TELEGRAM
# ======================

print("Sending to Telegram...")
# Твой оригинальный рабочий метод сборки URL
url = f"https://api.telegram.org{BOT_TOKEN}/sendPhoto"

payload = {
    "chat_id": CHAT_ID,
    "photo": image_url,
    "caption": post
}

r = requests.post(url, data=payload)
print("Status:", r.status_code)

if r.status_code != 200:
    print("Photo failed, sending text")
    requests.post(
        f"https://api.telegram.org{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": post}
    )

print("=== DONE ===")
