import requests
from bs4 import BeautifulSoup
import urllib.parse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

target = "https://www.nbc.gov.kh/index.php"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

response = requests.get(target, headers=headers, verify=False, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')

print(f"--- កំពុងស្វែងរក Link ក្នុង {target} ---")
count = 0
for a in soup.find_all('a', href=True):
    href = a['href'].strip()
    text = a.get_text(strip=True)
    full_url = urllib.parse.urljoin(target, href)
    
    # បង្ហាញតែ Link ណាដែលមានអក្សរ និងមិនមែនជា javascript ឬ #
    if text and not href.startswith(('#', 'javascript:')):
        print(f"[{count+1}] Text: {text[:35]} | URL: {full_url}")
        count += 1