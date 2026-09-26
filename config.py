import os
import json
from dotenv import load_dotenv

load_dotenv()

# AI Provider Settings
keys_json = os.getenv("GEMINI_API_KEYS", "[]")

try:
    # Try parsing as JSON array
    GEMINI_API_KEYS = json.loads(keys_json)
except Exception:
    # Fallback to comma separated string if JSON parsing fails
    GEMINI_API_KEYS = [k.strip() for k in keys_json.split(",") if k.strip()]

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Storage Settings (Save all URLs into ONE consolidated file)
OUTPUT_FILE = "data/khmer_articles.jsonl"

# Quality Thresholds (Optimized for LLM Training Datasets)
MIN_TEXT_LENGTH = 150  # Filter out tiny 1-line stubs so LLM training dataset has real paragraphs
MIN_KHMER_RATIO = 0.50

# HTTP Settings
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_TIMEOUT = 15