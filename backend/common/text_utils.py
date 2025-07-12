# Purpose: basic text cleaning to improve cosine-similarity hits
import re

def normalize_text(text: str) -> str:
    """
    • Removes punctuation
    • Converts to lowercase
    • Shrinks multiple spaces
    """
    cleaned = re.sub(r"[^\w\s]", " ", text)   # drop punctuation
    cleaned = re.sub(r"\s+", " ", cleaned)    # collapse spaces
    return cleaned.lower().strip()
