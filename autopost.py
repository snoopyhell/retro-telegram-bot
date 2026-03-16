import requests
import os
import random
import json
import urllib.parse

print("=== RETRO BOT ULTRA+ START ===")

# ================= CONFIG =================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
Ты пишешь посты для Telegram канала про ретро-игры.

Стиль:
— коротко (600–900 символов)
— описывай геймплей
— особенности игры
— механики
— чем она запомнилась игрокам
— минимум ностальгии
— без вступлений типа "Помню как..."
— живой игровой стиль

Формат:
🎮 Название
описание
2-4 коротких абзаца
в конце хештеги
"""

# ================= LOAD TOPICS =================

with open("topics.txt", "r", encoding="utf-8") as f:
    games = [x.strip() for x in f.readlines() if x.strip()]

# ===== anti repeat =====
USED_FILE = "used_games.json"

if os.path.exists(USED_FILE):
    used = json.load(open(USED_FILE))
else:
    used = []

available = [g for g in games if g not in used]

if not available:
    used = []
    available = games

game = random.choice(available)
used.append(game)

json.dump(used, open(USED_FILE, "w"))

print("Selected:", game)

# ================= PLATFORM TAGS =================

def platform_tags(name):
    return "#retrogaming #retro #sega #90s"

tags = platform_tags(game)

# ================= IMAGE SEARCH =================

SYSTEMS = [
    "Sega - Mega Drive - Genesis",
    "Nintendo - Super Nintendo Entertainment System",
    "Nintendo - Nintendo Entertainment System",
    "Sony - PlayStation",
]

REGIONS = ["(World)", "(USA)", "(Europe)", "(Japan)", ""]

def image_exists(url):
    try:
        r = requests.head(url, timeout=10)
        return r.status_code == 200
    except:
        return False

def find_image(game):
    encoded = urllib.parse.quote(game)

    for system in SYSTEMS:
        base = f"https://raw.githubusercontent.com/libretro-thumbnails/{urllib.parse.quote(system)}/Named_Boxarts"

        for region in REGIONS:
            name = f"{encoded}%20{urllib.parse.quote(region)}" if region else encoded
            url = f"{base}/{name}.png"

            print("Checking:", url)

            if image_exists(url):
                print("IMAGE FOUND")
                return url

    return None

image_url = find_image(game)

if not image_url:
    print("No image found — text only mode")

# ================= GENERATE TEXT =================

print("Generating text...")

prompt = f"Напиши пост про игру {game}"

response = requests.post(
    OPENROUTER_URL,
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    },
    timeout=120
)

print("OpenRouter status:", response.status_code)

data = response.json()
text = data["choices"][0]["message"]["content"].strip()

text += f"\n\n{tags}"

print("Text generated")

# ================= TELEGRAM POST =================

print("Sending to Telegram...")

def send_photo():
    return requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": text[:1024],
            "parse_mode": "HTML"
        },
        timeout=60
    )

def send_text():
    return requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        },
        timeout=60
    )

if image_url:
    tg = send_photo()

    # fallback если Telegram не смог обработать картинку
    if not tg.ok:
        print("Image failed → fallback to text")
        tg = send_text()
else:
    tg = send_text()

print("Telegram status:", tg.status_code)
print("Telegram response:", tg.text)

if not tg.ok:
    raise Exception("Telegram post failed")

print("✅ POST SUCCESS")
print("=== RETRO BOT ULTRA+ END ===")
