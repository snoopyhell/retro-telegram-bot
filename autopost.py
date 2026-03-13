import requests
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": "Напиши ностальгический пост для Telegram про Sega или PS1. Тёплый стиль 90-х, 700-900 символов, добавь вопрос в конце."
            }
        ]
    }
)

text = response.json()["choices"][0]["message"]["content"]

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": text
    }
)
