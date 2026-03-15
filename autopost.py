import requests
import os
import random
import urllib.parse
import json
import re

print("=== RETRO BOT ULTRA STARTED ===")

# Получаем ключи и убираем лишние пробелы/символы
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

# Проверка токена (самая частая ошибка)
if not BOT_TOKEN or not CHAT_ID:
    print("ERROR: BOT_TOKEN or CHAT_ID is empty!")
    exit(1)

# ======================
# LOAD TOPICS
# ======================
try:
    with open("topics.txt", "r", encoding="utf-8") as f:
        topics = [t.strip() for t in f.readlines() if t.strip()]
except:
    topics = ["Sonic the Hedgehog"]

USED_FILE = "used_games.json"
used_games = []
if os.path.exists(USED_FILE):
    try:
        with open(USED_FILE, "r", encoding="utf-8") as f:
            used_games = json.load(f)
    except: pass

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
# IMAGE SYSTEM
# ======================
def get_game_image(game_name):
    try:
        query = urllib.parse.quote(f"{game_name} Sega Genesis Box Art")
        # Исправлен URL Bing
        search_url = f"https://www.bing.com{query}"
        res = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        match = re.search(r'murl&quot;:&quot;(http[^&]+)&quot;', res.text)
        if match:
            return match.group(1)
    except: pass
    
    # Fallback на GitHub (исправлен путь)
    base = "https://raw.githubusercontent.com"
    name = urllib.parse.quote(game_name.replace(":", " _")) + ".png"
    return base + name

image_url = get_game_image(game)
print(f"Image URL: {image_url}")

# ======================
# GENERATE POST
# ======================
prompt = f"Напиши очень короткий ностальгический пост про игру {game} для Sega. 3 предложения без эмодзи."
text = f"{game}\nКлассика золотой эпохи Sega, которую мы проходили на выходных."

try:
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
        timeout=20
    )
    # Исправлено чтение ответа
    result = response.json()
    if 'choices' in result:
        text = result['choices'][0]['message']['content']
except Exception as e:
    print(f"AI Error: {e}")

post = f"{text}\n\n#retro #sega #90s"[:1024]

# ======================
# SEND TO TELEGRAM (FIXED)
# ======================
# Собираем URL максимально надежно
base_url = f"https://api.telegram.org{BOT_TOKEN}"
photo_url = f"{base_url}/sendPhoto"
msg_url = f"{base_url}/sendMessage"

print("Sending...")
try:
    # Пробуем отправить фото
    r = requests.post(photo_url, data={"chat_id": CHAT_ID, "photo": image_url, "caption": post}, timeout=20)
    if r.status_code != 200:
        print(f"Photo failed ({r.status_code}): {r.text}")
        # Если фото не прошло, шлем только текст
        requests.post(msg_url, data={"chat_id": CHAT_ID, "text": post}, timeout=20)
    else:
        print("Success!")
except Exception as e:
    print(f"Telegram Error: {e}")

print("=== DONE ===")
