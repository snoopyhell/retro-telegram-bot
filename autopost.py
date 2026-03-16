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
# IMAGE SYSTEM
# ======================

def image_exists(url):
    try:
        r = requests.head(url, timeout=10)
        return r.status_code == 200
    except:
        return False


def get_game_image(game):

    base = "https://raw.githubusercontent.com/libretro-thumbnails/Sega - Mega Drive - Genesis/Named_Boxarts/"

    name1 = urllib.parse.quote(game) + ".png"
    url1 = base + name1

    if image_exists(url1):
        return url1

    # remove subtitles
    short = game.split(" - ")[0]
    name2 = urllib.parse.quote(short) + ".png"
    url2 = base + name2

    if image_exists(url2):
        return url2

    # fallback retro image
    return "https://upload.wikimedia.org/wikipedia/commons/3/3e/Sega-Genesis-Mk2-6button.jpg"


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
    "https://openrouter.ai/api/v1/chat/completions",
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

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

payload = {
    "chat_id": CHAT_ID,
    "photo": image_url,
    "caption": post
}

r = requests.post(url, data=payload)

print("Telegram status:", r.status_code)
print("Telegram response:", r.text)

# fallback text (очень редко)
if r.status_code != 200:

    print("Photo failed, sending text")

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": post
        }
    )

print("=== DONE ===")
