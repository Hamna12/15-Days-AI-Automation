# llm/ollama_client.py

import requests
from config import OLLAMA_URL, MODEL_NAME, MAX_CONTENT_CHARS

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt[:MAX_CONTENT_CHARS],
        "stream": False
    }

    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if res.status_code != 200:
            return ""
        return res.json().get("response", "").strip()
    except:
        return ""
