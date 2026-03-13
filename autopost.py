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
        "model": "gpt-4.1-mini",
        "messages": [
            {
                "role": "user",
                "content": "Напиши ностальгический пост для Telegram про Sega или PS1. 700–900 символов, тёплый стиль 90-х, добавь эмодзи и вопрос в конце."
            }
        ]
    }
)

data = response.json()

if "choices" not in data:
    raise Exception(f"OpenAI error: {data}")

text = data["choices"][0]["message"]["content"]

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": text
    }
)
