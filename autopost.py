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
# IMAGE SYSTEM (UPDATED)
# ======================

def get_game_image(game_name):
    # Пытаемся найти картинку через быстрый поиск DuckDuckGo (без ключей)
    try:
        search_query = f"{game_name} Sega Genesis Mega Drive box art"
        url = "https://duckduckgo.com"
        params = {'q': search_query, 'kl': 'wt-wt'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        res = requests.get(url, params=params, headers=headers, timeout=10)
        # Ищем прямые ссылки на изображения в ответе
        links = re.findall(r'(https?://[^\s<>"]+\.(?:jpg|jpeg|png))', res.text)
        
        if links:
            # Возвращаем первую подходящую картинку
            for link in links:
                if "box" in link.lower() or "front" in link.lower() or "ign" in link.lower():
                    return link
            return links[0]
    except Exception as e:
        print(f"Search failed: {e}")

    # ЗАПАСНОЙ ВАРИАНТ (Ваш старый метод с исправленным путем)
    base = "https://raw.githubusercontent.com"
    name = urllib.parse.quote(game_name.replace(":", " _")) + ".png"
    fallback_url = base + name
    
    # Если и это не вышло - общая картинка приставки
    return fallback_url

image_url = get_game_image(game)
print("Image selected:", image_url)

# ======================
# GENERATE POST
# ======================

prompt = f"""
Напиши короткий ностальгический пост про игру {game}.
Формат:
Название игры
3-4 предложения воспоминаний о ретро играх 90-х, игровых вечерах и атмосфере Sega.
Стиль: тёплая ностальгия, как воспоминание игрока, без эмодзи.
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
        "messages": [{"role": "user", "content": prompt}]
    },
    timeout=60
)

data = response.json()
text = data["choices"][0]["message"]["content"]
hashtags = "\n\n#retro #retrogaming #sega #segagenesis #90s #videogames"
post = (text + hashtags)[:1024]

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

if r.status_code != 200:
    print(f"Photo failed (Error {r.status_code}), sending text only. Response: {r.text}")
    requests.post(
        f"https://api.telegram.org{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": post}
    )

print("=== DONE ===")
