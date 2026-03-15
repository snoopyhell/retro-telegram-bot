import requests
import os
import random
import urllib.parse
import json
import re

print("=== RETRO BOT ULTRA STARTED ===")

# Переменные окружения
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

# ======================
# LOAD TOPICS
# ======================
try:
    with open("topics.txt", "r", encoding="utf-8") as f:
        topics = [t.strip() for t in f.readlines() if t.strip()]
    print(f"Topics loaded: {len(topics)}")
except FileNotFoundError:
    print("Error: topics.txt not found!")
    topics = ["Sonic the Hedgehog", "Mortal Kombat 3", "Streets of Rage 2"]

# ======================
# ANTI REPEAT SYSTEM
# ======================
USED_FILE = "used_games.json"
used_games = []
if os.path.exists(USED_FILE):
    with open(USED_FILE, "r", encoding="utf-8") as f:
        used_games = json.load(f)

available = [g for g in topics if g not in used_games]
if not available:
    used_games = []
    available = topics

game = random.choice(available)
used_games.append(game)

with open(USED_FILE, "w", encoding="utf-8") as f:
    json.dump(used_games, f)

print(f"Chosen game: {game}")

# ======================
# IMAGE SYSTEM (Bing + Libretro Fallback)
# ======================
def get_game_image(game_name):
    # Поиск через Bing (парсинг прямой ссылки из murl)
    try:
        query = urllib.parse.quote(f"{game_name} Sega Genesis Box Art")
        url = f"https://www.bing.com{query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        # Находим прямую ссылку в murl (media url)
        match = re.search(r'murl&quot;:&quot;(http[^&]+)&quot;', res.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Bing search failed: {e}")

    # Fallback на GitHub Libretro
    base = "https://raw.githubusercontent.com"
    # Форматирование названия под стандарт Libretro (пробелы заменяются на %20 автоматически)
    name = urllib.parse.quote(game_name.replace(":", " _")) + ".png"
    return base + name

image_url = get_game_image(game)
print(f"Image selected: {image_url}")

# ======================
# GENERATE POST
# ======================
prompt = f"Напиши короткий ностальгический пост про игру {game} на Sega. Название игры, затем 3-4 предложения воспоминаний. Без эмодзи, стиль теплой ностальгии."

print("Generating post...")
try:
    response = requests.post(
        "https://openrouter.ai",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
        json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]},
        timeout=30
    )
    data = response.json()
    text = data["choices"][0]["message"]["content"]
except Exception as e:
    print(f"OpenRouter Error: {e}")
    text = f"{game}\nПомню, как мы часами сидели перед пузатым телевизором, вставляя заветный картридж. Это было время чистой радости и азарта."

hashtags = "\n\n#retro #retrogaming #sega #segagenesis #90s"
post = (text + hashtags)[:1024]

# ======================
# SEND TO TELEGRAM
# ======================
print("Sending to Telegram...")
url_photo = f"https://api.telegram.org{BOT_TOKEN}/sendPhoto"
url_msg = f"https://api.telegram.org{BOT_TOKEN}/sendMessage"

# Сначала пробуем отправить фото
r = requests.post(url_photo, data={"chat_id": CHAT_ID, "photo": image_url, "caption": post})

if r.status_code != 200:
    print(f"Photo failed (Error {r.status_code}), sending text only. Response: {r.text}")
    requests.post(url_msg, data={"chat_id": CHAT_ID, "text": post})

print("=== DONE ===")
