import re
import requests
from bs4 import BeautifulSoup
import urllib3
import config

# Suppress insecure SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KHMER_MONTHS = r"(?:មករា|កុម្ភៈ|មីនា|មេសា|ឧសភា|មិថុនា|កក្កដា|សីហា|កញ្ញា|តុលា|វិច្ឆិកា|ធ្នូ)"
DATE_REGEX = re.compile(
    rf"(?:(?:ថ្ងៃ(?:ចន្ទ|អង្គារ|ពុធ|ព្រហស្បតិ៍|សុក្រ|សៅរ៍|អាទិត្យ)?\s*)?(?:ទី\s*)?[០-៩0-9]{{1,2}}(?:\s*|\s*[-/]\s*|\s*ខែ\s*){KHMER_MONTHS}(?:\s*|\s*[-/]\s*|,?\s*|\s*ឆ្នាំ\s*)[០-៩0-9]{{4}}|[០-៩0-9]{{4}}[-/][០-៩0-9]{{1,2}}[-/][០-៩0-9]{{1,2}}|[០-៩0-9]{{1,2}}[-/][០-៩0-9]{{1,2}}[-/][០-៩0-9]{{4}})",
    re.IGNORECASE
)

# Unwanted layout / footer classes to decompose
UNWANTED_SELECTORS = [
    'header', 'footer', 'nav', 'aside', 'form', 'svg', 'noscript', 'script', 'style',
    '.td-footer-template-wrap', '.td-footer-wrap', '.td-sub-footer-wrap', '.td-menu-socials-wrap',
    '.td-post-sharing', '.td-post-sharing-bottom', '.td-post-sharing-top',
    '.footer', '.site-footer', '.sub-footer', '.widget', '.sidebar', '.breadcrumb',
    '.social-share', '.share-box', '.live-stream', '.comments', '.related-posts'
]


def extract_publication_date(soup: BeautifulSoup, text: str) -> str:
    """
    Attempts to extract the publication date from metadata, <time> tags, class attributes, or text.
    """
    # 1. Check <time> tag
    time_tag = soup.find('time')
    if time_tag:
        if time_tag.get('datetime'):
            return time_tag['datetime'].strip()
        tag_text = time_tag.get_text(strip=True)
        if tag_text:
            return tag_text

    # 2. Check meta tags
    meta_keys = [
        ('property', 'article:published_time'),
        ('property', 'og:published_time'),
        ('name', 'publish_date'),
        ('name', 'date'),
        ('name', 'pubdate'),
        ('itemprop', 'datePublished'),
        ('name', 'article:published_time')
    ]
    for attr, key in meta_keys:
        meta = soup.find('meta', {attr: key})
        if meta and meta.get('content'):
            return meta['content'].strip()

    # 3. Check HTML elements with date classes
    date_el = soup.find(class_=re.compile(
        r'\b(date|post-date|entry-date|published|created|news-date|publish-date|headline-date)\b', re.I
    ))
    if date_el:
        d_text = date_el.get_text(strip=True)
        match = DATE_REGEX.search(d_text)
        if match:
            return match.group(0).strip()
        if len(d_text) < 50 and any(c.isdigit() for c in d_text):
            return d_text

    # 4. Match regex pattern in text content
    if text:
        match = DATE_REGEX.search(text[:2000])
        if match:
            return match.group(0).strip()

    return ""


def fetch_and_extract(url: str) -> dict:
    """
    Fetches URL via HTTP. Falls back to Playwright if it's a JS-heavy SPA.
    Extracts article title, publication date, category, and body text.
    Skips PDF binary text extraction to preserve pure HTML datasets.
    """
    if url.lower().endswith('.pdf'):
        return {"is_pdf": True, "title": "", "text": "", "date": "", "category": "", "url": url}

    try:
        headers = {
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'km,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=config.REQUEST_TIMEOUT,
            verify=False
        )
        response.raise_for_status()

        # Detect PDF by Content-Type header
        if 'application/pdf' in response.headers.get('Content-Type', '').lower():
            return {"is_pdf": True, "title": "", "text": "", "date": "", "category": "", "url": url}

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # Check if it looks like a client-side rendered SPA
        text_content = soup.get_text(strip=True)
        is_spa = len(text_content) < 150 and (soup.find(id='root') or soup.find(id='app'))

        if is_spa:
            print(f"[THINKING] SPA detected at {url}. Falling back to Playwright...")
            html = _fetch_with_playwright(url)
            soup = BeautifulSoup(html, 'html.parser')

        # Extract specific article title
        # (prioritize h1, headline, or article title classes over general page title)
        title = ""
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text(strip=True):
            title = h1_tag.get_text(strip=True)
        else:
            headline_tag = soup.find(class_=re.compile(
                r'\b(headline|article-title|post-title|entry-title|news-title|title-detail|tdb-title-text)\b', re.I
            ))
            if headline_tag and headline_tag.get_text(strip=True):
                title = headline_tag.get_text(strip=True)
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()

        # Extract category if present
        category = ""
        category_meta = soup.find('meta', {'property': 'article:section'})
        if category_meta and category_meta.get('content'):
            category = category_meta['content'].strip()

        # Extract publication date BEFORE decomposing layout tags
        raw_text_snippet = soup.get_text(separator=' ', strip=True)
        date = extract_publication_date(soup, raw_text_snippet)

        # Decompose unwanted layout, footer, header, social, and widget tags
        for selector in UNWANTED_SELECTORS:
            for el in soup.select(selector):
                el.decompose()

        # Extract article body (targeted priority search for article content containers)
        article_container = (
            soup.find('div', class_=re.compile(
                r'\b(td-post-content|tdb_single_content|entry-content|article-content|post-content|content-text|article-body|detail-content|news-detail)\b', re.I
            )) or
            soup.find('article') or
            soup.find('main') or
            soup.find('div', class_=re.compile(r'\b(content|post-body|main-content|story-body)\b', re.I))
        )

        if article_container:
            body_text = article_container.get_text(separator=' ', strip=True)
        else:
            body_text = soup.get_text(separator=' ', strip=True)

        return {
            "is_pdf": False,
            "title": title,
            "text": body_text,
            "date": date,
            "category": category,
            "url": url,
            "html": html
        }
    except Exception as e:
        return {"error": str(e), "url": url}


def _fetch_with_playwright(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=config.USER_AGENT)
            page.goto(url, wait_until='networkidle', timeout=config.REQUEST_TIMEOUT * 1000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"[PLAYWRIGHT ERROR] Could not render via Playwright: {e}")
        return ""