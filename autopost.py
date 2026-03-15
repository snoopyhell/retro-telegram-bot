import requests
import os
import random
import urllib.parse
import json
import re

print("=== RETRO BOT ULTRA STARTED ===")

# Читаем переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# ======================
# LOAD TOPICS
# ======================
try:
    with open("topics.txt", "r", encoding="utf-8") as f:
        topics = [t.strip() for t in f.readlines() if t.strip()]
    print(f"Topics loaded: {len(topics)}")
except FileNotFoundError:
    topics = ["Sonic the Hedgehog", "Mortal Kombat 3", "Streets of Rage 2"]
    print("Warning: topics.txt not found, using defaults")

# ======================
# ANTI REPEAT SYSTEM
# ======================
USED_FILE = "used_games.json"
used_games = []
if os.path.exists(USED_FILE):
    try:
        with open(USED_FILE, "r", encoding="utf-8") as f:
            used_games = json.load(f)
    except:
        pass

available = [g for g in topics if g not in used_games]
if not available:
    available = topics
    used_games = []

game = random.choice(available)
used_games.append(game)

with open(USED_FILE, "w", encoding="utf-8") as f:
    json.dump(used_games, f)

print(f"Chosen game: {game}")

# ======================
# IMAGE SYSTEM (BING SEARCH)
# ======================
def get_game_image(game_name):
    try:
        # СТРОГО ПРОВЕРЕННЫЙ URL ДЛЯ BING
        query = urllib.parse.quote(f"{game_name} Sega Genesis Box Art")
        search_url = f"https://www.bing.com{query}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(search_url, headers=headers, timeout=15)
        
        # Регулярка для поиска прямых ссылок на фото
        links = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', res.text)
        if links:
            return links[0]
    except Exception as e:
        print(f"Image Search failed: {e}")
    
    # Запасная картинка, если поиск не сработал
    return "https://upload.wikimedia.org"

image_url = get_game_image(game)
print(f"Image selected: {image_url}")

# ======================
# GENERATE POST (OPENROUTER)
# ======================
prompt = f"Напиши короткий ностальгический пост про игру {game} на Sega Genesis. Название и 3-4 предложения воспоминаний игрока из 90-х. Без эмодзи, стиль теплой ностальгии."
final_text = f"{game}\nПомню, как мы часами сидели перед телевизором, проходя этот шедевр."

try:
    # ПРОВЕРЕННЫЙ ENDPOINT OPENROUTER
    api_url = "https://openrouter.ai"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        # СТРОГО: Индекс [0] обязателен!
        final_text = data["choices"][0]["message"]["content"]
        print("Text generated successfully")
    else:
        print(f"AI Error: Status {response.status_code}, Response: {response.text}")
except Exception as e:
    print(f"AI Critical Failure: {e}")

hashtags = "\n\n#retro #sega #90s #videogames"
post = (final_text + hashtags)[:1024]

# ======================
# SEND TO TELEGRAM
# ======================
print("Sending to Telegram...")
# СТРОГО ПРОВЕРЕННЫЙ URL TELEGRAM
tg_photo_url = f"https://api.telegram.org{BOT_TOKEN}/sendPhoto"
tg_msg_url = f"https://api.telegram.org{BOT_TOKEN}/sendMessage"

try:
    r = requests.post(tg_photo_url, data={
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": post
    }, timeout=30)
    
    if r.status_code == 200:
        print("SUCCESS: Post sent with image!")
    else:
        print(f"Telegram Photo failed (Status {r.status_code}): {r.text}")
        # Если фото не прошло, отправляем просто текст
        requests.post(tg_msg_url, data={"chat_id": CHAT_ID, "text": post}, timeout=30)
        print("Sent as text only.")
except Exception as e:
    print(f"Telegram send error: {e}")

print("=== DONE ===")
