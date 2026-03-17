import requests
import random
import os
import time

print("=== SEGA AUTO BOT START ===")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

# -------------------------
# LOAD GAMES
# -------------------------

if not os.path.exists("games.txt"):
    raise Exception("games.txt not found")

with open("games.txt", encoding="utf-8") as f:
    games = [g.strip() for g in f.readlines() if g.strip()]

if not games:
    raise Exception("games.txt empty")

# -------------------------
# SAFE RAWG REQUEST
# -------------------------

def safe_json_request(url):
    try:
        r = requests.get(url, timeout=15)

        if r.status_code != 200:
            print("RAWG bad status:", r.status_code)
            return None

        if not r.text.strip():
            print("RAWG empty response")
            return None

        return r.json()

    except Exception as e:
        print("RAWG request error:", e)
        return None

# -------------------------
# FIND BEST IMAGE (IMPROVED)
# -------------------------

def get_best_image(game):
    # Очищаем название от лишних символов
    clean_name = game.split('(')[0].split('[')[0].strip()
    
    search_variants = [
        clean_name,
        clean_name.split(":")[0] if ":" in clean_name else clean_name,
        clean_name.replace("-", " "),
        clean_name.replace("The ", ""),
    ]
    
    # Удаляем дубликаты
    search_variants = list(dict.fromkeys(search_variants))
    
    print(f"Searching for: {clean_name}")
    
    for name in search_variants:
        # Сначала пробуем точный поиск
        url = (
            f"https://api.rawg.io/api/games"
            f"?key={RAWG_API_KEY}"
            f"&search={name}"
            f"&search_precise=true"
            f"&page_size=3"
        )
        
        data = safe_json_request(url)
        
        if data and data.get("results"):
            for game_data in data["results"]:
                # Проверяем наличие изображения
                img = game_data.get("background_image")
                if img:
                    # Пытаемся получить изображение в более высоком качестве
                    if img.endswith(('.jpg', '.png', '.jpeg')):
                        # Заменяем на более качественную версию
                        high_quality_img = img.replace('/media/', '/media/resize/')
                        print(f"Found image for: {game_data['name']}")
                        return high_quality_img
        
        # Если точный поиск не дал результатов, пробуем обычный
        url = (
            f"https://api.rawg.io/api/games"
            f"?key={RAWG_API_KEY}"
            f"&search={name}"
            f"&page_size=5"
        )
        
        data = safe_json_request(url)
        
        if not data:
            continue
        
        for game_data in data.get("results", []):
            # Проверяем релевантность названия
            game_title = game_data.get("name", "").lower()
            search_term = name.lower()
            
            # Если название содержит поисковый запрос или наоборот
            if search_term in game_title or game_title in search_term:
                img = game_data.get("background_image")
                if img:
                    print(f"Found image for: {game_data['name']}")
                    return img
    
    return None

# -------------------------
# GENERATE PROPER TAGS
# -------------------------

def generate_tags(game_name, platform="SEGA"):
    # Базовая очистка названия
    clean_name = game_name.split('(')[0].split('[')[0].strip()
    
    # Разбиваем на слова для тегов
    words = clean_name.lower().split()
    
    # Основные теги
    tags = ["#retrogaming", f"#{platform.lower()}"]
    
    # Добавляем тег из первых двух слов названия
    if len(words) >= 2:
        game_tag = f"#{words[0]}{words[1]}".replace("-", "").replace(":", "")
    elif len(words) == 1:
        game_tag = f"#{words[0]}".replace("-", "").replace(":", "")
    else:
        game_tag = "#game"
    
    tags.append(game_tag)
    
    # Добавляем специфические теги для SEGA
    sega_tags = {
        "mega drive": "#megadrive",
        "genesis": "#genesis",
        "sega cd": "#segacd",
        "32x": "#sega32x",
        "game gear": "#gamegear",
        "master system": "#mastersystem",
        "dreamcast": "#dreamcast",
        "saturn": "#saturn"
    }
    
    for key, tag in sega_tags.items():
        if key in game_name.lower():
            tags.append(tag)
            break
    else:
        tags.append("#megadrive")  # тег по умолчанию
    
    # Добавляем тег жанра, если сможем определить
    genre_tags = get_game_genre(game_name)
    if genre_tags:
        tags.extend(genre_tags)
    
    return " ".join(tags)

# -------------------------
# GET GAME GENRE (OPTIONAL)
# -------------------------

def get_game_genre(game_name):
    try:
        clean_name = game_name.split('(')[0].strip()
        url = (
            f"https://api.rawg.io/api/games"
            f"?key={RAWG_API_KEY}"
            f"&search={clean_name}"
            f"&page_size=1"
        )
        
        data = safe_json_request(url)
        
        if data and data.get("results"):
            genres = data["results"][0].get("genres", [])
            if genres:
                genre = genres[0].get("name", "").lower()
                genre_map = {
                    "action": "#action",
                    "adventure": "#adventure",
                    "rpg": "#rpg",
                    "shooter": "#shooter",
                    "platformer": "#platformer",
                    "racing": "#racing",
                    "sports": "#sports",
                    "fighting": "#fighting",
                    "puzzle": "#puzzle",
                    "strategy": "#strategy"
                }
                return [genre_map.get(genre, "")]
    except:
        pass
    return []

# -------------------------
# TRY MULTIPLE GAMES
# -------------------------

image_url = None
selected_game = None
game_info = None

random.shuffle(games)

for candidate in games[:15]:  # try 15 games max
    print(f"Trying: {candidate}")
    
    img = get_best_image(candidate)
    
    if img:
        selected_game = candidate
        image_url = img
        break
    
    time.sleep(1)  # Небольшая задержка между запросами

if not image_url:
    raise Exception("No valid image found after retries")

print(f"Selected: {selected_game}")
print("Image OK")

# -------------------------
# PROMPT TYPES (IMPROVED)
# -------------------------

prompts = [
    f"""Напиши пост об игре {selected_game} для SEGA.
В посте расскажи:
- Краткое описание игры
- Особенности геймплея
- Почему в нее стоит поиграть сейчас

Тон: ностальгический, но информативный.
Объем: 300-400 символов.
В конце добавь вопрос к аудитории.

Не используй markdown, только plain text.""",

    f"""Расскажи интересный факт об игре {selected_game} для SEGA.
Что в ней было уникального для своего времени?
Почему игроки ее запомнили?

Кратко, емко, 250-300 символов.
Задай вопрос читателям в конце.""",

    f"""Сравни {selected_game} с современными играми похожего жанра.
Что SEGA-версия делала лучше?
Что было ограничено технически?

200-300 символов, закончи вопросом."""
]

prompt = random.choice(prompts)

# -------------------------
# GENERATE TEXT
# -------------------------

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/your-repo",  # Замените на свой репозиторий
    "X-Title": "SEGA Auto Poster"
}

try:
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 300
        },
        timeout=30
    )
    
    data = resp.json()
    
    if "error" in data:
        print(f"API Error: {data['error']}")
        # Fallback текст
        text = f"Игра {selected_game} для SEGA. Классика, которая заслуживает внимания! А вы играли в эту игру? {generate_tags(selected_game)}"
    else:
        generated_text = data["choices"][0]["message"]["content"].strip()
        
        # Генерируем теги
        tags = generate_tags(selected_game)
        
        # Убираем возможные дубли тегов из сгенерированного текста
        if "#" in generated_text:
            # Если теги уже есть в тексте, оставляем только текст без тегов
            text_parts = generated_text.split('#')
            generated_text = text_parts[0].strip()
        
        # Объединяем текст с тегами
        text = f"{generated_text}\n\n{tags}"
        
        # Ограничиваем длину
        if len(text) > 900:
            text = text[:880] + "...\n\n" + tags

except Exception as e:
    print(f"Generation error: {e}")
    # Fallback текст
    text = f"Игра {selected_game} для SEGA. Классика, которая заслуживает внимания! А вы играли в эту игру? {generate_tags(selected_game)}"

print("Text generated")

# -------------------------
# SEND TO TELEGRAM
# -------------------------

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

payload = {
    "chat_id": CHAT_ID,
    "photo": image_url,
    "caption": text
}

try:
    r = requests.post(telegram_url, data=payload, timeout=30)
    print(f"Telegram: {r.status_code}")
    
    if not r.ok:
        print(f"Error response: {r.text}")
        
        # Fallback - пробуем отправить без фото, только текст
        if r.status_code == 400:  # Bad request (возможно проблема с фото)
            print("Trying to send without photo...")
            text_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            text_payload = {
                "chat_id": CHAT_ID,
                "text": text
            }
            r2 = requests.post(text_url, data=text_payload)
            print(f"Text only result: {r2.status_code}")
            
except Exception as e:
    print(f"Telegram send error: {e}")
    raise

print("=== POST SUCCESS ===")
