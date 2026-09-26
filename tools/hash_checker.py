import os


def is_url_processed(url_hash: str, domain: str) -> bool:
    """
    Checks if a given url_hash is already present in the processed_urls.txt for the domain.
    Uses a set-based lookup for O(1) performance on large record files.
    """
    record_file = os.path.join("records", domain, "processed_urls.txt")
    if not os.path.exists(record_file):
        return False

    with open(record_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Each line is: "<hash> <url>"
            if line.split(' ', 1)[0].strip() == url_hash:
                return True
    return False
