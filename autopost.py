import requests
import os
import random
import re
from urllib.parse import quote

print("=== RETRO BOT ULTRA START ===")

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

# ---------------- LOAD GAMES ----------------

with open("topics.txt", "r", encoding="utf-8") as f:
    all_games = [g.strip() for g in f if g.strip()]

posted = set()
if os.path.exists("posted.txt"):
    with open("posted.txt", "r", encoding="utf-8") as f:
        posted = set(x.strip() for x in f)

available = [g for g in all_games if g not in posted]

if not available:
    print("All games posted. Resetting history.")
    open("posted.txt", "w").close()
    available = all_games

game = random.choice(available)
print("Selected:", game)

# ---------------- CLEAN NAME ----------------

def clean_name(name):
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\[.*?\]", "", name)
    name = name.replace(":", "")
    return name.strip()

clean_game = clean_name(game)

# ---------------- IMAGE SEARCH ----------------

systems = [
    "Sega - Mega Drive - Genesis",
    "Sony - PlayStation",
    "Nintendo - Super Nintendo Entertainment System",
    "Nintendo - Nintendo Entertainment System"
]

def find_image(title):
    variants = [
        title,
        title.replace("IV", "4"),
        title.replace("III", "3"),
        title.replace("II", "2"),
    ]

    for system in systems:
        for v in variants:
            url = f"https://raw.githubusercontent.com/libretro-thumbnails/{quote(system)}/Named_Boxarts/{quote(v)}.png"
            print("Checking image:", url)

            try:
                r = requests.head(url, timeout=10)
                if r.status_code == 200:
                    print("IMAGE FOUND")
                    return url
            except:
                pass

    return None

image_url = find_image(clean_game)

if not image_url:
    raise Exception("No valid image found — stopping post")

# ---------------- GENERATE POST ----------------

prompt = f"""
Напиши пост про игру {game}.

Стиль:
— описание геймплея
— ключевые механики
— особенности уровня или боевой системы
— чем игра отличалась

Добавь:
Жанр:
Год выхода:
Платформа:

6 предложений максимум.
"""

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
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

if response.status_code != 200:
    raise Exception("OpenRouter error: " + response.text)

data = response.json()

text = data["choices"][0]["message"]["content"].strip()

if not text:
    raise Exception("Empty text from AI")

caption = f"🎮 {game}\n\n{text}\n\n#retrogaming #sega #ps1 #retro"

# ---------------- SEND TELEGRAM ----------------

print("Sending post...")

tg = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
    data={
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption
    },
    timeout=60
)

print("Telegram:", tg.text)

tg_data = tg.json()

if not tg_data.get("ok"):
    raise Exception("Telegram failed: " + tg.text)

# ---------------- SAVE HISTORY ----------------

with open("posted.txt", "a", encoding="utf-8") as f:
    f.write(game + "\n")

print("Post published successfully")
print("=== RETRO BOT ULTRA END ===")
