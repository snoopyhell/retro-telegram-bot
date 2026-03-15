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
    topics = [t.strip() for f_line in f.readlines() if (t := f_line.strip())]

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
# IMAGE SYSTEM (SEARCH FROM WEB)
# ======================

def get_game_image(game_name):
    # Поиск прямой ссылки на обложку через Bing Images
    try:
        query = urllib.parse.quote(f"{game_name} Sega Genesis Mega Drive box art")
        search_url = f"https://www.bing.com{query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        res = requests.get(search_url, headers=headers, timeout=15)
        # Ищем в коде страницы ссылки на изображения (параметр murl)
        links = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', res.text)
        
        if links:
            # Возвращаем первую найденную картинку
            return links[0]
            
    except Exception as e:
        print(f"Web search failed: {e}")

    # Если поиск не удался — возвращаем стандартное фото приставки
    return "https://upload.wikimedia.org"


image_url = get_game_image(game)
print("Image selected:", image_url)

# ======================
# GENERATE POST
# ======================

prompt = f"""
Напиши короткий ностальгический пост про игру {game}.

Формат:
Название игры
3-4 предложения воспоминаний о ретро играх 90-х,
игровых вечерах и атмосфере Sega.

Стиль:
тёплая ностальгия
как воспоминание игрока
без эмодзи
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

print("OpenRouter status:", response.status_code)

data = response.json()
# ИСПРАВЛЕНО: Добавлен индекс [0], чтобы не было ошибки JSON
text = data["choices"][0]["message"]["content"]

print("Text generated")

# ======================
# HASHTAGS
# ======================

hashtags = """
#retro #retrogaming
#sega #segagenesis
#90s #videogames
"""

post = f"{text}\n{hashtags}"
post = post[:1024]

# ======================
# SEND TO TELEGRAM
# ======================

print("Sending photo...")

url = f"https://api.telegram.org{BOT_TOKEN}/sendPhoto"

payload = {
    "chat_id": CHAT_ID,
    "photo": image_url,
    "caption": post
}

r = requests.post(url, data=payload)

print("Telegram status:", r.status_code)

# Если фото не отправилось (битая ссылка из поиска), отправляем только текст
if r.status_code != 200:
    print(f"Photo failed ({r.text}), sending text only")
    requests.post(
        f"https://api.telegram.org{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": post
        }
    )

print("=== DONE ===")
