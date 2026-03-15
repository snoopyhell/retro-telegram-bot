import requests
import os
import random
import urllib.parse
import json
import re

print("=== RETRO BOT ULTRA STARTED ===")

# Читаем переменные и СТРОГО чистим их от пробелов и кавычек
BOT_TOKEN = str(os.environ.get("BOT_TOKEN", "")).strip().replace(" ", "")
CHAT_ID = str(os.environ.get("CHAT_ID", "")).strip().replace(" ", "")
OPENROUTER_API_KEY = str(os.environ.get("OPENROUTER_API_KEY", "")).strip()

# ТЕСТ ПЕРЕМЕННЫХ (в логах GitHub будут звезды, но мы увидим длину)
print(f"DEBUG: Token length: {len(BOT_TOKEN)}")
print(f"DEBUG: Chat ID length: {len(CHAT_ID)}")

if len(BOT_TOKEN) < 5:
    print("ERROR: BOT_TOKEN is too short or missing!")
    exit(1)

# ======================
# LOAD TOPICS
# ======================
try:
    with open("topics.txt", "r", encoding="utf-8") as f:
        topics = [t.strip() for t in f.readlines() if t.strip()]
except:
    topics = ["Sonic the Hedgehog"]

game = random.choice(topics)
print(f"Chosen game: {game}")

# ======================
# IMAGE SYSTEM (Упрощенный путь)
# ======================
def get_game_image(game_name):
    # Прямая ссылка на GitHub репозиторий (фикс пути)
    base = "https://raw.githubusercontent.com"
    safe_name = urllib.parse.quote(game_name.replace(":", " _")) + ".png"
    return base + safe_name

image_url = get_game_image(game)
print(f"Image URL: {image_url}")

# ======================
# GENERATE POST
# ======================
# Упрощаем запрос к ИИ, чтобы не падал
text = f"{game}\nНастоящая классика 16-битной эпохи. Помним эти вечера у экрана."

try:
    api_url = "https://openrouter.ai"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": f"Напиши 2 предложения ностальгии про игру {game} на Sega"}]
    }
    response = requests.post(api_url, headers=headers, json=data, timeout=20)
    
    if response.status_code == 200:
        res_json = response.json()
        text = res_json['choices'][0]['message']['content']
    else:
        print(f"AI API Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"AI Logic Error: {e}")

post = f"{text}\n\n#retro #sega"[:1024]

# ======================
# SEND TO TELEGRAM (БЕЗОПАСНАЯ СБОРКА)
# ======================
print("Sending...")

# Используем метод запроса без f-строки в самом URL, чтобы избежать ошибок парсинга
tg_url = "https://api.telegram.org" + BOT_TOKEN + "/sendPhoto"

payload = {
    "chat_id": CHAT_ID,
    "photo": image_url,
    "caption": post
}

try:
    r = requests.post(tg_url, data=payload, timeout=30)
    if r.status_code == 200:
        print("SUCCESS: Post sent to Telegram!")
    else:
        print(f"FAILED: Status {r.status_code}")
        print(f"Response: {r.text}")
        
        # Попытка №2: Отправка только текста, если фото не подошло
        msg_url = "https://api.telegram.org" + BOT_TOKEN + "/sendMessage"
        requests.post(msg_url, data={"chat_id": CHAT_ID, "text": post})
except Exception as e:
    print(f"CRITICAL ERROR: {e}")

print("=== DONE ===")
