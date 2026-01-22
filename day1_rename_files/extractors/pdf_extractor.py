# extractors/pdf_extractor.py

import PyPDF2
from pdf2image import convert_from_path
import pytesseract

def extract_text_from_pdf(path: str) -> str:
    text = ""

    # Try normal PDF text
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except:
        pass

    if text.strip():
        return text.strip()

    # OCR fallback (scanned PDF)
    try:
        pages = convert_from_path(path)
        for page in pages:
            text += pytesseract.image_to_string(page)
    except:
        return ""

    return text.strip()
