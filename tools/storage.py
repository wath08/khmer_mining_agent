import json
import os
from .url_hasher import hash_url
import config


def save_article(domain: str, article_data: dict):
    """
    Saves the verified article data into ONE consolidated JSONL file (data/khmer_articles.jsonl).
    """
    file_path = getattr(config, 'OUTPUT_FILE', 'data/khmer_articles.jsonl')

    # Fix: os.path.dirname("data/khmer_articles.jsonl") = "data" which is correct,
    # but if OUTPUT_FILE were a bare filename with no directory, dirname returns ""
    # and makedirs("") raises FileNotFoundError. Guard against that case.
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    # Standard output format
    record = {
        "id": hash_url(article_data["url"]),
        "domain": domain,
        "title": article_data.get("title", ""),
        "date": article_data.get("date", ""),
        "category": article_data.get("category", ""),
        "url": article_data["url"],
        "text": article_data.get("text", "")
    }

    with open(file_path, "a", encoding="utf-8") as f:
        # ensure_ascii=False keeps Khmer characters readable in JSON
        json_line = json.dumps(record, ensure_ascii=False)
        f.write(json_line + "\n")
