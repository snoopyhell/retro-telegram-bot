import requests
import os
import random
import urllib.parse
import json
import re

print("=== RETRO BOT ULTRA STARTED ===")

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

# ======================
# LOAD TOPICS
# ======================
with open("topics.txt", "r", encoding="utf-8") as f:
    topics = [t.strip() for t in f.readlines() if t.strip()]

used_games = []
if os.path.exists("used_games.json"):
    with open("used_games.json", "r", encoding="utf-8") as f:
        used_games = json.load(f)

available = [g for g in topics if g not in used_games]
if not available:
    available = topics
    used_games = []

game = random.choice(available)
used_games.append(game)
with open("used_games.json", "w", encoding="utf-8") as f:
    json.dump(used_games, f)

print(f"Chosen game: {game}")

# ======================
# IMAGE SYSTEM (FIXED URLS)
# ======================
def get_game_image(game_name):
    # 1. Поиск через Bing (Исправлен путь /images/search)
    try:
        query = urllib.parse.quote(f"{game_name} Sega Genesis Box Art")
        search_url = f"https://www.bing.com{query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(search_url, headers=headers, timeout=10)
        match = re.search(r'murl&quot;:&quot;(http[^&]+)&quot;', res.text)
        if match:
            return match.group(1)
    except:
        pass

    # 2. Запасной путь GitHub (Исправлен слеш после .com)
    base = "https://raw.githubusercontent.com"
    name = urllib.parse.quote(game_name.replace(":", " _")) + ".png"
    return base + name

image_url = get_game_image(game)
print(f"Image URL: {image_url}")

# ======================
# GENERATE POST
# ======================
prompt = f"Напиши короткий ностальгический пост про игру {game} на Sega Genesis. Название игры, затем 3-4 предложения воспоминаний игрока из 90-х. Без эмодзи, стиль теплой ностальгии."

text = f"{game}\nПомню, как часами сидели перед телевизором, проходя этот шедевр." # Дефолтный текст

try:
    # Исправлен полный путь к API
    response = requests.post(
        "https://openrouter.ai",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        text = data["choices"][0]["message"]["content"]
except Exception as e:
    print(f"AI Error: {e}")

hashtags = "\n\n#retro #retrogaming #sega #90s"
post = (text + hashtags)[:1024]

# ======================
# SEND TO TELEGRAM (FIXED /bot)
# ======================
# ВАЖНО: Добавлен слеш перед bot и после него
url_photo = f"https://api.telegram.org{BOT_TOKEN}/sendPhoto"
url_msg = f"https://api.telegram.org{BOT_TOKEN}/sendMessage"

print("Sending...")
try:
    r = requests.post(url_photo, data={"chat_id": CHAT_ID, "photo": image_url, "caption": post})
    if r.status_code != 200:
        print(f"Photo failed: {r.text}")
        requests.post(url_msg, data={"chat_id": CHAT_ID, "text": post})
except Exception as e:
    print(f"Telegram Error: {e}")

print("=== DONE ===")
