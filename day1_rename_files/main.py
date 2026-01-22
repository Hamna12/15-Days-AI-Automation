# main.py

import os
from config import INPUT_DIR, OUTPUT_DIR, SUPPORTED_IMAGES, SUPPORTED_TEXT
from extractors.pdf_extractor import extract_text_from_pdf
from extractors.image_extractor import extract_text_from_image
from extractors.text_extractor import extract_text_from_text_file
from processors.cleaner import clean_text
from processors.filename_generator import generate_filename
from utils.file_ops import copy_with_dedup

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in os.listdir(INPUT_DIR):
    path = os.path.join(INPUT_DIR, file)
    if not os.path.isfile(path):
        continue

    ext = file.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        text = extract_text_from_pdf(path)
    elif ext in SUPPORTED_IMAGES:
        text = extract_text_from_image(path)
    elif ext in SUPPORTED_TEXT:
        text = extract_text_from_text_file(path)
    else:
        continue

    if not text:
        print(f"⚠️ No text found: {file}")
        continue

    cleaned = clean_text(text)
    filename = generate_filename(cleaned)

    if not filename:
        print(f"❌ LLM failed: {file}")
        continue

    copy_with_dedup(path, OUTPUT_DIR, f"{filename}.{ext}")
    print(f"✅ {file} → {filename}.{ext}")
