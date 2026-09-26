import hashlib

def hash_url(url: str) -> str:
    """
    Converts a URL string into a unique MD5 hash string.
    """
    return hashlib.md5(url.encode('utf-8')).hexdigest()
