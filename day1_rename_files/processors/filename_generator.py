# processors/filename_generator.py

import re
from llm.ollama_client import call_ollama

def build_prompt(content: str) -> str:
    return f"""
You are a local AI assistant whose job is to rename files based on their meaning.

Your task is to analyze the content and decide how a careful human would name this file.

INSTRUCTIONS:
1. Identify what this content represents (purpose, context, or intent).
2. Identify the most important concept or subject.
3. Generate a concise filename that clearly represents the content.

RULES:
- Do NOT ask the user questions
- Do NOT invent information
- Do NOT explain your reasoning
- Use snake_case only
- Use 2–4 words maximum
- Avoid generic words (file, document, image, screenshot, data)
- Avoid dates unless they are critical to meaning
- Output ONLY the filename (no extension, no quotes, no extra text)

CONTENT:
{content}
"""


def generate_filename(clean_text: str) -> str | None:
    response = call_ollama(build_prompt(clean_text))

    if not response:
        return None

    name = response.strip().lower()
    name = re.sub(r"[^\w_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    # Safety check: too short or meaningless
    if len(name) < 5:
        return None

    return name

