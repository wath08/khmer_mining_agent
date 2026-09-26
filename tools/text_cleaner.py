import re

KHMER_CONSONANTS = "កខគឃងចឆជឈញដឋឌឍណតថទធនបផពភមយរលវសហឡអ"
KHMER_DEPENDENT_VOWELS = "ាិីឹឺុូួើឿៀេែៃោៅ"
KHMER_DIACRITICS = ["ំ", "ះ", "ៈ", "៉", "៊", "់", "៌", "៍", "៎", "៏", "័", "៑", "្", "៓", "៝"]

VALID_KHMER_STREAM_REGEX = re.compile(r"[^\u1780-\u17ff\u19e0-\u19ff0-9a-zA-Z\s.,;:()/%«»“”\"\'\-?!\n#@+=<>]")

# Social media, footer, live stream, and boilerplate patterns to remove
BOILERPLATE_PATTERNS = [
    # 1. Remove all Web URLs
    r"https?://[^\s]+",
    r"www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*",
    
    # 2. Breadcrumbs and navigation leftovers
    r"^(?:ព័ត៌មាន\s*)?(?:ទំព័រដើម\s*(?:>|»|/|\||\s)*\s*)*(?:ព័ត៌មាន|សេចក្តីជូនដំណឹង|សុន្ទរកថា|សេចក្តីប្រកាសព័ត៌មាន|\s*)*(?:>|»|/|\||\s)*",
    r"[-–—•*]*\s*ទាញយក(?:សេចក្តីជូនដំណឹង|ឯកសារ|ព័ត៌មាន|ឯកសារភ្ជាប់)?\s*[^.។៕\n]*",
    r"[-–—•*]*\s*មើលឯកសារ(?:ពេញលេញ)?\s*[^.។៕\n]*",
    
    # 3. Footer widgets, Live Streams, and Cool App
    r"(?:ការផ្សាយបន្តផ្ទាល់|Live Streams|វិទ្យុ|បណ្តាញសង្គម|Cool App)[^.។៕\n]*",
    r"[-–—•*]*\s*(?:Facebook|YouTube|Telegram|TikTok|Instagram|Twitter|Vimeo|VKontakte)\s*(?:Cool App)?[^.។៕\n]*",
    
    # 4. Social channels and keywords
    r"[-–—•*]*\s*តេឡេក្រាម\s*[^.។៕\n]*",
    r"[-–—•*]*\s*គេហទំព័រ\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ទិកតុក\s*[^.។៕\n]*",
    r"[-–—•*]*\s*អិច\s*[^.។៕\n]*",
    r"[-–—•*]*\s*យូ\s*ធូប\s*[^.។៕\n]*",
    r"[-–—•*]*\s*យូធូប\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ហ្វេសប៊ុក\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ឆាណែល\s*តេឡេក្រាម\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ទំព័រ\s*ហ្វេសប៊ុក\s*[^.។៕\n]*",
    r"[-–—•*]*\s*បណ្ដាញ\s*សង្គម\s*ផ្លូវការ\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ផ្សាយ\s*បន្ត\s*ដោយ\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ចែករំលែក\s*:\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ចុច\s*Link\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ចុច\s*ទីនេះ\s*[^.។៕\n]*",
    r"[-–—•*]*\s*អាន\s*ព័ត៌មាន\s*បន្ថែម\s*[^.។៕\n]*",
    r"[-–—•*]*\s*រូបភាព\s*:\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ប្រភព\s*:\s*[^.។៕\n]*",
    r"[-–—•*]*\s*ទូរស័ព្ទ\s*លេខ\s*:\s*[\d\s/\-]+",
    r"[-–—•*]*\s*(?:Email|អ៊ីមែល|សារអេឡិចត្រូនិច)\s*:\s*[^\s]+"
]

def clean_khmer_text(text: str) -> str:
    """
    Cleans and standardizes Khmer text based on predefined regex rules.
    """
    if not text:
        return ""

    # Remove social media keywords, boilerplate, footer text, and URLs
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Fix broken words
    fixes = {
        r'ដែ\s*ល': 'ដែល',
        r'ក្នុ\s*ង': 'ក្នុង',
        r'ឡើ\s*ើង': 'ឡើង',
        r'ខ្លួ\s*ន': 'ខ្លួន',
        r'ឱ្យ\s*យ': 'ឱ្យ',
        r'រដ្ឋឋបាល': 'រដ្ឋបាល',
        r'ផ្នែកម្មន្តសាល': 'ផ្នែកកម្មន្តសាល',
        r'ផ្នែកម្មសិទ្ធិ': 'ផ្នែកកម្មសិទ្ធិ',
        r'(?<![ក-អ])ក្កដា': 'កក្កដា',
        r'\u17d2+': '\u17d2'
    }
    for pattern, replacement in fixes.items():
        text = re.sub(pattern, replacement, text)

    # Replace straight quotes with formal Khmer quotes
    text = re.sub(r'"([^"]*)"', r'«\1»', text)

    # Remove invalid characters using the specific regex
    text = VALID_KHMER_STREAM_REGEX.sub('', text)

    # Cleanup extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()

    return text
