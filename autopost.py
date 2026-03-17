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
# FALLBACK IMAGE SOURCES
# -------------------------

def get_fallback_image(game_name):
    """Получить изображение из альтернативных источников"""
    
    # Очищаем название
    clean_name = game_name.split('(')[0].split('[')[0].strip()
    clean_name = clean_name.replace(" ", "%20")
    
    # 1. Пробуем получить из Google Custom Search (если есть API ключ)
    google_api_key = os.getenv("GOOGLE_API_KEY")  # Опционально
    google_cx = os.getenv("GOOGLE_CX")  # Опционально
    
    if google_api_key and google_cx:
        try:
            google_url = f"https://www.googleapis.com/customsearch/v1?q={clean_name}+SEGA+Megadrive&cx={google_cx}&key={google_api_key}&searchType=image&num=1"
            r = requests.get(google_url, timeout=10)
            if r.ok:
                data = r.json()
                if "items" in data and len(data["items"]) > 0:
                    return data["items"][0]["link"]
        except:
            pass
    
    # 2. Пробуем получить из TheGamesDB (бесплатно, без ключа)
    try:
        # Сначала ищем игру
        search_url = f"https://api.thegamesdb.net/v1/Games/ByGameName?apikey=YOUR_API_KEY&name={clean_name}"
        # Примечание: для TheGamesDB нужна регистрация, но есть бесплатный ключ
        # Пока используем заглушку
        pass
    except:
        pass
    
    # 3. Используем placeholder изображения с текстом игры
    # Это запасной вариант, если ничего не нашлось
    return f"https://via.placeholder.com/800x400/1e1e2f/ffffff?text={clean_name}+SEGA"

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
            f"&page_size=5"
        )
        
        data = safe_json_request(url)
        
        if data and data.get("results"):
            for game_data in data["results"]:
                # Пробуем получить разные типы изображений
                img = game_data.get("background_image")
                if not img:
                    img = game_data.get("background_image_additional")
                if not img:
                    img = game_data.get("clip")
                
                if img:
                    print(f"Found image for: {game_data['name']}")
                    return img
        
        # Если точный поиск не дал результатов, пробуем обычный
        url = (
            f"https://api.rawg.io/api/games"
            f"?key={RAWG_API_KEY}"
            f"&search={name}"
            f"&page_size=10"
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
                if not img:
                    img = game_data.get("background_image_additional")
                
                if img:
                    print(f"Found image for: {game_data['name']}")
                    return img
    
    # Если ничего не нашли в RAWG, пробуем fallback
    print("RAWG returned no images, trying fallback...")
    fallback_img = get_fallback_image(clean_name)
    
    return fallback_img

# -------------------------
# DOWNLOAD AND REUPLOAD IMAGE (для надежности)
# -------------------------

def download_and_send_image(image_url, game_name):
    """Скачивает изображение и отправляет его в Telegram как файл"""
    try:
        # Скачиваем изображение
        img_response = requests.get(image_url, timeout=15)
        if img_response.ok:
            # Сохраняем временно
            temp_filename = f"temp_{int(time.time())}.jpg"
            with open(temp_filename, 'wb') as f:
                f.write(img_response.content)
            
            # Отправляем через Telegram API как файл
            telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            
            with open(temp_filename, 'rb') as f:
                files = {'photo': f}
                data = {'chat_id': CHAT_ID}
                r = requests.post(telegram_url, files=files, data=data)
            
            # Удаляем временный файл
            os.remove(temp_filename)
            
            return r.ok
    except Exception as e:
        print(f"Error downloading/sending image: {e}")
    
    return False

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
        game_tag = f"#{words[0]}{words[1]}".replace("-", "").replace(":", "").replace("'", "")
    elif len(words) == 1:
        game_tag = f"#{words[0]}".replace("-", "").replace(":", "").replace("'", "")
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
    
    return " ".join(tags)

# -------------------------
# TRY MULTIPLE GAMES
# -------------------------

image_url = None
selected_game = None

random.shuffle(games)

for candidate in games[:20]:  # try 20 games max
    print(f"Trying: {candidate}")
    
    img = get_best_image(candidate)
    
    if img:
        selected_game = candidate
        image_url = img
        break
    
    time.sleep(1)  # Небольшая задержка между запросами

if not image_url:
    # Если совсем нет картинок, создаем заглушку
    selected_game = random.choice(games)
    clean_name = selected_game.split('(')[0].split('[')[0].strip()
    image_url = f"https://via.placeholder.com/800x400/1e1e2f/ffffff?text={clean_name.replace(' ', '+')}+SEGA"
    print(f"Using placeholder for: {selected_game}")

print(f"Selected: {selected_game}")
print(f"Image URL: {image_url}")

# -------------------------
# PROMPT TYPES
# -------------------------

prompts = [
    f"""Напиши пост об игре {selected_game} для SEGA.
Расскажи:
- О чем игра
- Особенности геймплея
- Почему она запомнилась

Объем: 300-400 символов.
В конце задай вопрос.
Без markdown.""",

    f"""Интересный факт об игре {selected_game} для SEGA.
Что в ней было уникального?
Почему стоит поиграть сегодня?

Кратко, 200-300 символов.
Закончи вопросом.""",

    f"""Сравни {selected_game} с другими играми SEGA.
Что в ней особенного?
Какой ваш опыт?

~300 символов, вопрос в конце."""
]

prompt = random.choice(prompts)

# -------------------------
# GENERATE TEXT
# -------------------------

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
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
        text = f"Игра {selected_game} для SEGA. Классика, которая заслуживает внимания! А вы играли в эту игру?"
    else:
        generated_text = data["choices"][0]["message"]["content"].strip()
        
        # Генерируем теги
        tags = generate_tags(selected_game)
        
        # Убираем возможные дубли тегов
        if "#" in generated_text:
            text_parts = generated_text.split('#')
            generated_text = text_parts[0].strip()
        
        text = f"{generated_text}\n\n{tags}"
        
        if len(text) > 900:
            text = text[:880] + "...\n\n" + tags

except Exception as e:
    print(f"Generation error: {e}")
    text = f"Игра {selected_game} для SEGA. Классика, которая заслуживает внимания! А вы играли в эту игру? {generate_tags(selected_game)}"

print("Text generated")

# -------------------------
# SEND TO TELEGRAM
# -------------------------

print("Sending to Telegram...")

# Пробуем отправить с URL
telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

payload = {
    "chat_id": CHAT_ID,
    "photo": image_url,
    "caption": text
}

try:
    r = requests.post(telegram_url, data=payload, timeout=30)
    print(f"Telegram response: {r.status_code}")
    
    if not r.ok:
        print(f"Error: {r.text}")
        
        # Если URL не работает, пробуем скачать и отправить
        print("Trying to download and reupload image...")
        if download_and_send_image(image_url, selected_game):
            print("Image downloaded and sent successfully")
            
            # Отправляем текст отдельно (если фото отправилось без текста)
            text_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            text_payload = {
                "chat_id": CHAT_ID,
                "text": text
            }
            requests.post(text_url, data=text_payload)
        else:
            # Если совсем не получается с фото, шлем только текст
            print("Sending text only...")
            text_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            text_payload = {
                "chat_id": CHAT_ID,
                "text": text
            }
            r2 = requests.post(text_url, data=text_payload)
            print(f"Text only result: {r2.status_code}")
            
except Exception as e:
    print(f"Error: {e}")
    # Пробуем отправить только текст
    try:
        text_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        text_payload = {
            "chat_id": CHAT_ID,
            "text": text
        }
        requests.post(text_url, data=text_payload)
    except:
        pass

print("=== POST ATTEMPT COMPLETED ===")
