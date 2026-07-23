import re
from ..models import ImageObject, PageObjects, Product, TextBlock
from .page_parser import extract_price, is_price
from .layout_engine import nearby_text

SKIP_TEXT = re.compile(
    r"\b(?:catalog|product catalog|items shown|all information|available while|sales are final|"
    r"refunds|exchanges|returns|features?|dimensions?|edition size|purchase limit|retail|"
    r"soft enamel|hard enamel|mystery boxes?|pin store|sunday|monday|tuesday|wednesday|"
    r"thursday|friday|saturday)\b",
    re.I,
)
DIMS = re.compile(r"\s+DIMS?:\s*.*$", re.I)
COLLECTION_ITEM = re.compile(r"^([A-Z0-9 '&’.-]{3,})\s+-\s+(.+)$")


def _clean_item(text: str) -> str:
    text = DIMS.sub("", text).strip(" -;:•\t")
    text = re.sub(r"\s+", " ", text)
    return text


def _is_item_text(block: TextBlock) -> bool:
    text = block.text.strip()
    if not text or is_price(text) or SKIP_TEXT.search(text):
        return False
    if "DIMS" in text.upper():
        return True
    if len(text) <= 80 and block.bbox[1] > 200:
        letters = [c for c in text if c.isalpha()]
        return bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.65
    return False


def _nearest_image(block: TextBlock, images: list[ImageObject]) -> ImageObject | None:
    if not images:
        return None
    bx = (block.bbox[0] + block.bbox[2]) / 2
    by = (block.bbox[1] + block.bbox[3]) / 2

    def score(image: ImageObject) -> float:
        x0, y0, x1, y1 = image.bbox
        ix = (x0 + x1) / 2
        iy = (y0 + y1) / 2
        vertical_penalty = 0 if by >= y0 - 40 else 250
        return abs(bx - ix) + abs(by - iy) * 0.6 + vertical_penalty

    return min(images, key=score)


def _collection_and_item(text: str, page_collection: str) -> tuple[str, str]:
    item = _clean_item(text)
    match = COLLECTION_ITEM.match(item)
    if match:
        collection = match.group(1).strip(" -")
        item = match.group(2).strip(" -")
        return collection, item
    return page_collection, item


def _page_price(page: PageObjects) -> str:
    return next((extract_price(block.text) for block in page.text_blocks if is_price(block.text)), "")


def products_from_page(page: PageObjects, store: str, date: str, collection: str) -> list[Product]:
    products: list[Product] = []
    page_price = _page_price(page)
    seen: set[tuple[str, str, str]] = set()

    item_blocks = [block for block in page.text_blocks if _is_item_text(block)]
    for block in item_blocks:
        image = _nearest_image(block, page.images)
        product_collection, item = _collection_and_item(block.text, collection)
        if not item:
            continue
        local_text = nearby_text(page, image.bbox) if image else []
        price = next((extract_price(text.text) for text in local_text if is_price(text.text)), page_price)
        key = (product_collection.lower(), item.lower(), price.lower())
        if key in seen:
            continue
        seen.add(key)
        products.append(
            Product(
                store=store,
                date=date,
                collection=product_collection,
                item=item,
                price=price,
                notes="",
                image_path=image.image_path if image else None,
                confidence=(0.45 if item else 0) + (0.35 if price else 0) + (0.20 if image else 0),
            )
        )

    if products:
        return products

    for image in page.images:
        ordered = nearby_text(page, image.bbox)
        price = next((extract_price(block.text) for block in ordered if is_price(block.text)), page_price)
        item = next((_clean_item(block.text) for block in ordered if _is_item_text(block)), "")
        notes = "; ".join(block.text for block in ordered if block.text not in {item, price} and block.text and len(block.text) < 160)[:500]
        score = (0.45 if item else 0) + (0.35 if price else 0) + (0.20 if image else 0)
        products.append(Product(store, date, collection, item, price, notes, image_path=image.image_path, confidence=score))
    return products
