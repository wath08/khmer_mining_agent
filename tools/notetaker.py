import os
from .url_hasher import hash_url

def record_processed_url(url: str, domain: str):
    """
    Records a successfully scraped URL into records/{domain}/processed_urls.txt
    """
    _append_record(domain, "processed_urls.txt", f"{hash_url(url)} {url}")

def record_skipped_url(url: str, domain: str, reason: str):
    """
    Records a skipped URL (e.g., too short, low khmer ratio).
    """
    _append_record(domain, "skipped_urls.txt", f"{hash_url(url)} {url} - REASON: {reason}")

def record_retry_link(url: str, domain: str, error: str):
    """
    Records a URL that failed to fetch and needs a retry.
    """
    _append_record(domain, "retry_links.txt", f"{hash_url(url)} {url} - ERROR: {error}")

def record_pdf_link(url: str, source_page: str, domain: str):
    """
    Records a discovered PDF link with its source page.
    """
    record_str = f"PDF_URL:     {url}\nSOURCE_PAGE: {source_page}\n" + ("-" * 60)
    _append_record(domain, "pdf_urls.txt", record_str)

def _append_record(domain: str, filename: str, content: str):
    """Helper to ensure directory exists and append to file."""
    dir_path = os.path.join("records", domain)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, filename)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(content + "\n")
