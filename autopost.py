import requests
import os
import random

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

print("Bot started")

with open("topics.txt", "r", encoding="utf-8") as f:
    topics = f.read().splitlines()

print("Topics loaded:", topics)

topic = random.choice(topics)

print("Selected topic:", topic)

prompt = f"Напиши короткий ностальгический пост про {topic} и ретро-игры."

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

print("OpenRouter response:", response.text)

data = response.json()

text = data["choices"][0]["message"]["content"]

print("Generated text:", text)

r = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": text}
)

print("Telegram response:", r.text)
