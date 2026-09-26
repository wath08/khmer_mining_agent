from agent import MiningAgent
import config

TARGET_SITES = [
    "https://mcfa.gov.kh/km/news/",
]

START_PAGE = 1
PAGES_PER_RUN = 3
REQUEST_DELAY = 0.3

if __name__ == "__main__":
    print("==================================================")
    print("   Autonomous Khmer Data Mining Agent v1.0")
    print("==================================================")
    print(f"[CONFIG] Start Page: {START_PAGE}")
    print(f"[CONFIG] Pages Per Run: {PAGES_PER_RUN}")
    print(f"[CONFIG] Request Delay: {REQUEST_DELAY}s")
    print(f"[CONFIG] Min Text Length: {config.MIN_TEXT_LENGTH} chars")
    print("==================================================")
    
    agent = MiningAgent()
    
    for site in TARGET_SITES:
        print(f"\n=======================================================")
        print(f"  [TARGET] Starting data mining campaign for: {site}")
        print(f"=======================================================")
        
        # Loop through pages for paginated sites
        for page in range(START_PAGE, START_PAGE + PAGES_PER_RUN):
            if "page" in site or "nbc.gov.kh" in site or "pressocm" in site:
                if "?" in site:
                    paginated_url = f"{site}&page={page}"
                else:
                    paginated_url = f"{site}?page={page}"
            else:
                paginated_url = f"{site}page/{page}/" if page > 1 else site
                
            print(f"\n[PAGE] Preparing to extract articles from page {page}...")
            
            agent.run(start_url=paginated_url, delay=REQUEST_DELAY)