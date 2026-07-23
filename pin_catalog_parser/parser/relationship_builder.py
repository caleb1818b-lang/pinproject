import re
from ..models import PageObjects, Product
from .page_parser import extract_price, is_price
from .layout_engine import nearby_text

def products_from_page(page: PageObjects, store: str, date: str, collection: str) -> list[Product]:
    products = []
    for image in page.images:
        ordered = nearby_text(page, image.bbox)
        price = next((extract_price(b.text) for b in ordered if is_price(b.text)), "")
        item = next((b.text for b in ordered if not is_price(b.text) and len(b.text) <= 100 and not re.search(r"\b(?:catalog|product catalog|limited|release|edition|features?|dimensions?|retail|soft enamel|mystery boxes?)\b", b.text, re.I)), "")
        notes = "; ".join(b.text for b in ordered if b.text not in {item, price} and b.text and len(b.text) < 160)[:500]
        score = (0.45 if item else 0) + (0.35 if price else 0) + (0.20 if image else 0)
        products.append(Product(store, date, collection, item, price, notes, confidence=score))
    return products
