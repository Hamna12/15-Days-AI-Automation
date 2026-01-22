# extractors/text_extractor.py

def extract_text_from_text_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except:
        return ""
