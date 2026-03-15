import requests
import os
import random

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

with open("topics.txt", "r", encoding="utf-8") as f:
    topics = f.read().splitlines()

with open("used_topics.txt", "r", encoding="utf-8") as f:
    used = set(f.read().splitlines())

available = [t for t in topics if t not in used]

if not available:
    available = topics
    open("used_topics.txt", "w").close()

topic = random.choice(available)

with open("used_topics.txt", "a", encoding="utf-8") as f:
    f.write(topic + "\n")

prompt = f"""
Напиши ностальгический пост про {topic}.
Стиль: воспоминания 90-х.
Тема: Sega и PlayStation 1.
Длина: 500–800 символов.
Добавь эмодзи и вопрос в конце.
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
    }
)

text = response.json()["choices"][0]["message"]["content"]

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": text}
)
