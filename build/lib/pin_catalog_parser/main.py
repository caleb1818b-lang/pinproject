import argparse
from pathlib import Path
import re
import os
import fitz
from PIL import Image
from .models import Product
from .ai.ollama_verifier import ollama_status

def text_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(text_value(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {text_value(v)}" for k, v in value.items())
    return str(value).strip()
def process(pdf: Path, output_dir: Path):
    from .parser.pdf_reader import read_pdf
    from .parser.page_parser import parse_first_page
    from .parser.relationship_builder import products_from_page
    from .parser.image_extractor import extract_images
    from .ai.ollama_verifier import verify_tile
    pages = read_pdf(pdf); store, date = parse_first_page(pages[0]) if pages else ("", "")
    images_dir = output_dir / pdf.stem / "images"; extract_images(pages, images_dir)
    products = []
    rendered_dir = output_dir / pdf.stem / "pages"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    source_doc = fitz.open(pdf)
    model_name = os.getenv("PIN_OLLAMA_MODEL", "qwen2.5vl:3b")
    print(f"  Loaded {len(pages)} pages; checking Ollama model={model_name}...", flush=True)
    if not ollama_status(model_name):
        raise RuntimeError(f"Required Ollama model unavailable: {model_name}")
    print("  Ollama page vision: enabled; fallback disabled", flush=True)
    collection = ""
    metadata = re.compile(r"(?:catalog|product|retail|edition|dimensions|features|store|january|february|march|april|may|june|july|august|september|october|november|december|sunday|monday|tuesday|wednesday|thursday|friday|saturday)", re.I)
    for page in pages:
        first_image_y = min((image.bbox[1] for image in page.images), default=page.height)
        candidates = [b for b in page.text_blocks if b.bbox[1] < first_image_y and b.bold and len(b.text) < 60 and not metadata.search(b.text) and not re.search(r"\$\s*\d", b.text)]
        if candidates:
            collection = max(candidates, key=lambda b: (b.font_size, -b.bbox[1])).text
        if page.number == 1:
            continue
        page_path = rendered_dir / f"page-{page.number:03d}.png"
        source_doc[page.number - 1].get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False).save(page_path)
        page_image = Image.open(page_path)
        width, height = page_image.size
        tile_width, tile_height = width // 2, height // 2
        tiles = []
        for row in range(2):
            for col in range(2):
                left = max(0, col * tile_width - 80); top = max(0, row * tile_height - 80)
                right = min(width, (col + 1) * tile_width + 80); bottom = min(height, (row + 1) * tile_height + 80)
                tile_path = rendered_dir / f"page-{page.number:03d}-tile-{row * 2 + col + 1}.jpg"
                page_image.crop((left, top, right, bottom)).resize(((right-left)//2, (bottom-top)//2)).convert("RGB").save(tile_path, quality=88)
                tiles.append(tile_path)
        print(f"  Page {page.number}/{len(pages)}: scanning {len(tiles)} overlapping vision tiles...", flush=True)
        page_context = {"Store": store, "Date": date, "Collection": collection, "Text": "\n".join(block.text for block in page.text_blocks)}
        ai_products = []
        for tile_number, tile_path in enumerate(tiles, 1):
            print(f"  Page {page.number}: tile {tile_number}/{len(tiles)}...", flush=True)
            ai_products.extend(verify_tile(tile_path, page_context))
        unique = {}
        for item in ai_products:
            if not isinstance(item, dict):
                continue
            normalized = {key: text_value(value) for key, value in item.items()}
            key = (normalized.get("Item", "").lower(), normalized.get("Price", "").lower())
            if key != ("", ""):
                unique[key] = normalized
        ai_products = list(unique.values())
        print(f"  Page {page.number}: Ollama found {len(ai_products)} unique products", flush=True)
        for item in ai_products:
            products.append(Product(text_value(item.get("Store")) or store, text_value(item.get("Date")) or date, text_value(item.get("Collection")) or collection, text_value(item.get("Item")), text_value(item.get("Price")), text_value(item.get("Notes")), confidence=0.98))
    source_doc.close()
    # Match extracted images back in page/image order.
    files = sorted(images_dir.glob("*") )
    for index, product in enumerate(products):
        product.image_path = files[index % len(files)] if files else None
    usable = []
    for product in products:
        if product.item.strip() or product.price.strip():
            product.notes = f"Source PDF: {pdf.name}; {product.notes}".strip(" ;")
            usable.append(product)
    return usable

def main():
    ap = argparse.ArgumentParser(description="Batch-convert Disney pin catalog PDFs to Excel")
    ap.add_argument("input", type=Path, help="PDF file or folder containing PDFs")
    ap.add_argument("-o", "--output", type=Path, default=Path("output"))
    args = ap.parse_args()
    if args.input.is_file():
        pdfs = [args.input] if args.input.suffix.lower() == ".pdf" else []
    else:
        pdfs = sorted((p for p in args.input.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"), key=lambda p: p.name.lower())
    args.output.mkdir(parents=True, exist_ok=True)
    all_products = []
    for pdf in pdfs:
        products = process(pdf, args.output)
        all_products.extend(products)
        print(f"{pdf.name}: {len(products)} products")
    from .excel.exporter import export
    export(all_products, args.output / "disney-pin-catalogue.xlsx")
    print(f"Combined workbook: {len(all_products)} products")

if __name__ == "__main__": main()
