import re
from ..models import PageObjects

PRICE = re.compile(r"\$\s*\d+(?:\.\d{2})?")
MONTH = re.compile(r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:\d{1,2},\s+)?\d{4}", re.I)

def parse_first_page(page: PageObjects) -> tuple[str, str]:
    texts = [b.text for b in page.text_blocks]
    date = next((MONTH.search(t).group(0) for t in texts if MONTH.search(t)), "")
    store = next((t.split("|")[0].strip() for t in texts if "pin store" in t.lower()), "")
    if not store and any("pin product catalog" in t.lower() for t in texts):
        store = "Disney Pin Store"
    return store, date

def extract_price(text: str) -> str:
    match = PRICE.search(text.replace("，", ","))
    return match.group(0).replace(" ", "") if match else ""

def is_price(text: str) -> bool: return bool(extract_price(text))
