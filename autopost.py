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

USED_FILE = "used_games.json"
if os.path.exists(USED_FILE):
    with open(USED_FILE, "r", encoding="utf-8") as f:
        used_games = json.load(f)
else:
    used_games = []

available = [g for g in topics if g not in used_games]
if not available:
    available = topics
    used_games = []

game = random.choice(available)
used_games.append(game)
with open(USED_FILE, "w", encoding="utf-8") as f:
    json.dump(used_games, f)

print("Chosen game:", game)

# ======================
# IMAGE SYSTEM
# ======================
def get_game_image(game):
    # Исправленный путь к репозиторию libretro
    base = "https://raw.githubusercontent.com"
    
    # В libretro ':' заменяется на ' _', а в URL пробелы должны быть %20
    clean_name = game.replace(":", " _")
    name_quoted = urllib.parse.quote(clean_name) + ".png"
    url = base + name_quoted

    try:
        r = requests.head(url, timeout=10)
        if r.status_code == 200:
            return url
    except:
        pass
    
    return "https://upload.wikimedia.org"

image_url = get_game_image(game)
print("Image selected:", image_url)

# ======================
# GENERATE POST
# ======================
prompt = f"Напиши короткий ностальгический пост про игру {game} на Sega. Название, затем 3 предложения воспоминаний. Без эмодзи."

print("Generating post...")
post_text = f"{game}\nПомню, как мы часами сидели перед телевизором, проходя этот шедевр." # Запасной текст

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
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        # ИСПРАВЛЕНО: добавлен индекс [0]
        post_text = data["choices"][0]["message"]["content"]
    else:
        print(f"OpenRouter Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Post generation failed: {e}")

hashtags = "\n\n#retro #sega #90s #videogames"
full_post = (post_text + hashtags)[:1024]

# ======================
# SEND TO TELEGRAM
# ======================
print("Sending...")
tg_url = f"https://api.telegram.org{BOT_TOKEN}/sendPhoto"

try:
    r = requests.post(tg_url, data={
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": full_post
    })
    
    if r.status_code != 200:
        print(f"Telegram Photo Error: {r.text}")
        requests.post(f"https://api.telegram.org{BOT_TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": full_post})
except Exception as e:
    print(f"Telegram critical error: {e}")

print("=== DONE ===")
