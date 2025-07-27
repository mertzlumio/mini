import requests
import json
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL

def call_mistral(prompt):
    system_prompt = """
You are a helpful assistant. Your job is to determine if the user's request contains a task that should be added to a to-do list.

If the user's request is a task, respond with a JSON object with two keys:
- "task": a string containing the task.
- "response": a string containing a friendly confirmation message.

If the user's request is not a task, respond with a JSON object with one key:
- "response": a string containing your response.

For example:
User: add milk to my shopping list
{"task": "buy milk", "response": "I've added 'buy milk' to your shopping list."}

User: I need to finish my report by Friday.
{"task": "finish report by Friday", "response": "Okay, I'll add 'finish report by Friday' to your to-do list."}

User: What's the weather like today?
{"response": "I can't check the weather, but I hope it's nice!"}

Note: Respond ONLY with raw JSON. DO NOT use markdown formatting like ```json.
"""
    try:
        res = requests.post(
            MISTRAL_URL,
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MISTRAL_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=15
        )
        res.raise_for_status()
        
        response_text = res.json()["choices"][0]["message"]["content"].strip()
        
        try:
            # Try to parse the response as JSON
            response_json = json.loads(response_text)
            return response_json
        except json.JSONDecodeError:
            # If it's not JSON, return it as a regular string in the expected format
            return {"response": response_text}

    except Exception as e:
        return {"response": f"⚠️ Mistral error: {str(e)}"}
