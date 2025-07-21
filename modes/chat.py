import requests
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL

def call_mistral(prompt):
    try:
        res = requests.post(
            MISTRAL_URL,
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MISTRAL_MODEL,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=15
        )
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Mistral error: {str(e)}"
