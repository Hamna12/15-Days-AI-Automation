# extractors/image_extractor.py

from PIL import Image
import pytesseract

def extract_text_from_image(path: str) -> str:
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img).strip()
    except:
        return ""
