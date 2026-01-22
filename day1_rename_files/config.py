# config.py

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:4b"

INPUT_DIR = "files_to_rename"
OUTPUT_DIR = "renamed_files"

SUPPORTED_IMAGES = ["png", "jpg", "jpeg", "bmp", "tiff", "gif"]
SUPPORTED_TEXT = ["txt", "md"]

MAX_CONTENT_CHARS = 1800
MIN_CONFIDENCE = 0.6
