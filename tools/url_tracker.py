import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

KHMER_MONTHS = r"(?:មករា|កុម្ភៈ|មីនា|មេសា|ឧសភា|មិថុនា|កក្កដា|សីហា|កញ្ញា|តុលា|វិច្ឆិកា|ធ្នូ)"
DATE_REGEX = re.compile(
    rf"(?:(?:ថ្ងៃ(?:ចន្ទ|អង្គារ|ពុធ|ព្រហស្បតិ៍|សុក្រ|សៅរ៍|អាទិត្យ)?\s*)?(?:ទី\s*)?[០-៩0-9]{{1,2}}(?:\s*|\s*[-/]\s*|\s*ខែ\s*){KHMER_MONTHS}(?:\s*|\s*[-/]\s*|,?\s*|\s*ឆ្នាំ\s*)[០-៩0-9]{{4}}|[០-៩0-9]{{4}}[-/][០-៩0-9]{{1,2}}[-/][០-៩0-9]{{1,2}}|[០-៩0-9]{{1,2}}[-/][០-៩0-9]{{1,2}}[-/][០-៩0-9]{{4}})",
    re.IGNORECASE
)

# Static navigation keywords to filter out of candidate articles
STATIC_KEYWORDS = {
    'about', 'contact', 'structure', 'mission', 'vision', 'history', 'organization',
    'terms', 'privacy', 'department', 'career', 'job', 'vacanc', 'internship',
    'staff', 'board_of_directors', 'branch', 'banknotes', 'coins', 'currency',
    'museum', 'hotline', 'social_network', 'working_at', 'facebook.com', 'twitter.com',
    'youtube.com', 't.me', 'telegram.me'
}

IGNORED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.css', '.js', '.zip', '.rar', '.mp4', '.mp3', '.pdf', '.doc', '.docx', '.xls', '.xlsx')

def extract_links(html: str, base_url: str) -> list[str]:
    """
    Extracts all valid URLs from the given HTML, normalized with the base_url.
    Ensures links are within the same domain.
    """
    candidates = extract_candidate_links(html, base_url)
    return [c["url"] for c in candidates]

def extract_candidate_links(html: str, base_url: str) -> list[dict]:
    """
    Extracts candidate links along with their anchor text and surrounding context (date hints).
    Provides rich context for the AI Agent to decide which links are actual news articles.
    """
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    base_domain = urlparse(base_url).netloc
    
    seen_urls = set()
    candidates = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].strip()
        if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            continue
            
        full_url = urljoin(base_url, href)
        parsed_full = urlparse(full_url)
        
        # Only keep links from the same domain
        if parsed_full.netloc != base_domain:
            continue
            
        clean_url = full_url.split('#')[0]
        if clean_url in seen_urls or clean_url.rstrip('/') == base_url.rstrip('/'):
            continue
            
        url_lower = clean_url.lower()
        if any(url_lower.endswith(ext) for ext in IGNORED_EXTENSIONS):
            continue

        seen_urls.add(clean_url)
        
        anchor_text = a_tag.get_text(separator=' ', strip=True)
        
        # Extract surrounding context (e.g., parent card, list item, table row, or paragraph)
        parent = a_tag.find_parent(['article', 'li', 'tr', 'td', 'div', 'p'])
        context_text = ""
        if parent:
            context_text = parent.get_text(separator=' ', strip=True)[:250]
        else:
            context_text = anchor_text
            
        # Check for date hint in context, <time> tag, or URL
        has_date_hint = bool(DATE_REGEX.search(context_text) or DATE_REGEX.search(clean_url))
        if not has_date_hint and parent:
            if parent.find('time') or parent.find(class_=re.compile(r'date|time|published|created', re.I)):
                has_date_hint = True
                
        # Check if URL looks like an obvious static menu link
        is_likely_static = any(kw in url_lower or kw in anchor_text.lower() for kw in STATIC_KEYWORDS)

        candidates.append({
            "url": clean_url,
            "text": anchor_text,
            "context": context_text,
            "has_date_hint": has_date_hint,
            "is_likely_static": is_likely_static
        })
        
    # Sort candidates: prioritize items with date hints and non-static items
    candidates.sort(key=lambda c: (not c.get("is_likely_static", False), c.get("has_date_hint", False)), reverse=True)

    return candidates
