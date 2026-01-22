# processors/cleaner.py

import re

def clean_text(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"[^A-Za-z0-9\s]", "", text)
    return text
