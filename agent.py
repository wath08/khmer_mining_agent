import time
import re
import urllib.parse
from tools import (
    hash_url, is_url_processed, record_processed_url, record_skipped_url,
    record_retry_link, record_pdf_link, extract_candidate_links, fetch_and_extract,
    clean_khmer_text, verify_text, save_article
)
import config

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class MiningAgent:
    def __init__(self):
        self.domain = ""
        self.visited = set()
        self.queue = []
        self.gemini_model = None

        if not getattr(config, 'GEMINI_API_KEY', None):
            print("[WARNING] GEMINI_API_KEY is not found in environment/.env. Will use heuristic fallback.")
        elif HAS_GEMINI:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model_name = getattr(config, 'GEMINI_MODEL', 'gemini-2.5-flash')
            model_name = model_name.replace("models/", "").strip()
            try:
                self.gemini_model = genai.GenerativeModel(model_name)
            except Exception as e:
                print(f"[WARNING] Could not initialize Gemini model '{model_name}': {e}. Falling back to heuristic.")
                self.gemini_model = None
        else:
            print("[WARNING] google-generativeai package is not installed.")

    def decide_news_links_with_ai(self, candidates: list[dict], current_url: str) -> list[str]:
        """
        The AI Agent inspects candidate links and makes the autonomous decision:
        Identifies which links are genuine individual news articles/announcements/speeches,
        and eliminates navigation/static links (About, Contact, Leadership, etc.).
        """
        if not candidates:
            return []

        # Filter out current URL and non-article files
        filtered_candidates = [
            c for c in candidates
            if c["url"].rstrip('/') != current_url.rstrip('/')
        ]

        if not filtered_candidates:
            return []

        # Separate candidates into non-static vs likely static
        non_static = [c for c in filtered_candidates if not c.get("is_likely_static", False)]
        likely_static = [c for c in filtered_candidates if c.get("is_likely_static", False)]

        # Take non-static first, up to 60 links to keep prompt concise and focused
        sample_candidates = non_static[:60] if non_static else likely_static[:40]

        print(f"\n[THINKING] Reviewing {len(sample_candidates)} candidate links on {current_url}...")
        print(f"[THINKING] Consulting Gemini to detect individual article pages...")

        candidates_text = ""
        for i, c in enumerate(sample_candidates, 1):
            date_info = "Detected Date Nearby" if c.get("has_date_hint") else "No Explicit Date"
            candidates_text += (
                f"{i}. URL: {c['url']}\n"
                f"   Title/Anchor: {c['text']}\n"
                f"   Context: {c['context'][:120]}\n"
                f"   Date Hint: {date_info}\n\n"
            )

        prompt = f"""You are an expert data mining agent analyzing a Cambodian government/news website.
Target Website: {current_url}

Below is a list of candidate links. Note that the Anchor Text and Context are primarily in the Khmer language:
{candidates_text}

Your Task:
1. Identify ONLY links that lead to SPECIFIC, INDIVIDUAL news articles, press releases, announcements, or speeches.
2. STRICTLY EXCLUDE:
   - Category hubs, index pages, or pagination links (e.g., 'news.php', 'page=2', '/category/').
   - Static organizational pages (e.g., About Us, Vision, Structure, Leadership, Contact, Services, Terms).
   - Social media, external links, or downloadable file links (PDFs, images).
3. First, provide a brief 1-2 sentence reasoning explaining your selection.
4. Then, output each approved URL on a new line EXACTLY prefixed with "APPROVED: ".
5. DO NOT use markdown code blocks (```), bullet points, or extra text. If no links are valid, output ONLY the reasoning.

Format Requirement:
REASONING: <brief reasoning here>
APPROVED: <url1>
APPROVED: <url2>
"""

        approved_urls = []

        # 1. Gemini AI Call
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(prompt)
                output = response.text.strip()

                reasoning = ""
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith("REASONING:"):
                        reasoning = line.replace("REASONING:", "").strip()
                    elif line.startswith("APPROVED:"):
                        url = line.replace("APPROVED:", "").strip()
                        if url and url.upper() != "NONE" and url.startswith("http"):
                            approved_urls.append(url)

                if reasoning:
                    print(f"[AI REASONING] {reasoning}")
                print(f"[AI DECISION] Approved {len(approved_urls)} individual articles to crawl down.")
                if approved_urls:
                    return approved_urls
            except Exception as e:
                print(f"[AI ERROR] Gemini request failed ({e}). Falling back to heuristic decision.")

        # 2. Intelligent Heuristic Fallback (Runs if Gemini fails, is unconfigured, or returned 0)
        print(f"[AI DECISION] (Heuristic Fallback) Filtering links based on date hints, query IDs, and article patterns...")
        for c in sample_candidates:
            if c.get("is_likely_static"):
                continue

            url_lower = c["url"].lower()

            # Match URLs with item IDs, info suffixes, date hints, or article slugs
            is_article_link = (
                c.get("has_date_hint") or
                any(k in url_lower for k in [
                    '_info.php', 'id=', 'article', 'post', 'view', 'detail',
                    'speeches_info', 'announcements_info', 'press_releases_info'
                ]) or
                (len(c["text"]) > 20 and not url_lower.endswith('.php'))
            )

            if is_article_link:
                approved_urls.append(c["url"])

        # Deduplicate while preserving order
        seen_app = set()
        deduped = []
        for u in approved_urls:
            if u not in seen_app:
                seen_app.add(u)
                deduped.append(u)

        print(f"[AI DECISION] Approved {len(deduped)} individual articles to crawl down.")
        return deduped

    def run(self, start_url: str, delay: float = 0.2):
        self.queue = [start_url]
        self.domain = urllib.parse.urlparse(start_url).netloc

        listing_pages = {start_url.rstrip('/'), start_url}

        print(f"\n[SYSTEM] Autonomous Mining Agent Initialized.")
        print(f"[TARGET] {self.domain} | Listing URL: {start_url}")
        model_label = (
            f"GEMINI ({getattr(config, 'GEMINI_MODEL', 'gemini-2.5-flash')})"
            if self.gemini_model else "HEURISTIC"
        )
        print(f"[BRAIN] {model_label}")
        print("-" * 50)

        articles_saved = 0

        # Listing-hub URL pattern matcher (compiled once per run, not per iteration)
        listing_hub_pattern = re.compile(
            r'/category/|/archives/category|/tag/|/tags/|/archive/'
            r'|/km/news/?$|/news/?$|/news_and_events/?$'
            r'|/press_releases/?$|/announcements/?$|/speeches/?$',
            re.IGNORECASE
        )

        while self.queue:
            current_url = self.queue.pop(0)

            if current_url in self.visited:
                continue

            self.visited.add(current_url)
            url_hashed = hash_url(current_url)

            print(f"\n[ACTION] Navigating to: {current_url}")

            # Check duplicate cache
            if is_url_processed(url_hashed, self.domain):
                print(f"[CACHE] URL {url_hashed[:8]}... already processed. Skipping.")
                continue

            # Fetch HTML
            data = fetch_and_extract(current_url)

            if "error" in data:
                print(f"[ERROR] Failed to fetch: {data['error']}")
                record_retry_link(current_url, self.domain, data['error'])
                continue

            if data.get("is_pdf"):
                print(f"[PDF DETECTED] Saving PDF link to records...")
                record_pdf_link(current_url, current_url, self.domain)
                continue

            # Extract Candidate Links on this page
            candidates = extract_candidate_links(data.get('html', ''), current_url)

            # Detect listing/hub pages: the start URL, paginated pages, category/archive/tag indexes
            is_listing_hub = (
                current_url.rstrip('/') in listing_pages or
                'page=' in current_url or
                bool(listing_hub_pattern.search(current_url))
            )

            if candidates and is_listing_hub:
                ai_approved_links = self.decide_news_links_with_ai(candidates, current_url)

                new_links_added = 0
                for link in ai_approved_links:
                    if link not in self.visited and link not in self.queue:
                        self.queue.append(link)
                        new_links_added += 1

                print(f"[ACTION] Added {new_links_added} individual article links to queue. Current Queue: {len(self.queue)}.")

            if is_listing_hub:
                print(f"[HUB PAGE] {current_url} is a listing/hub page. Crawling down to its articles. (Will NOT save hub to JSONL).")
                continue

            print(f"[ARTICLE PAGE] Extracting individual article details...")
            cleaned_text = clean_khmer_text(data.get('text', ''))

            print(f"[THINKING] Verifying quality constraints (Length >= {config.MIN_TEXT_LENGTH}, Khmer Ratio >= {config.MIN_KHMER_RATIO})...")
            verification = verify_text(cleaned_text)

            if verification["is_valid"]:
                date_str = data.get("date") or "N/A"
                print(f"[VERIFIED] Passed! Title: '{data.get('title', '')[:40]}...' | Date: {date_str}")
                data['text'] = cleaned_text
                data['date'] = date_str
                save_article(self.domain, data)
                record_processed_url(current_url, self.domain)
                print(f"[ACTION] Successfully saved individual article to data/{self.domain}.jsonl")
                articles_saved += 1
            else:
                print(f"[SKIPPED] {verification['reason']}")
                record_skipped_url(current_url, self.domain, verification['reason'])

            time.sleep(delay)

        print(f"\n[SYSTEM] Job completed for {self.domain}. Successfully mined {articles_saved} individual articles.")