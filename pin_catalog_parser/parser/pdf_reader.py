from pathlib import Path
import fitz
from ..models import ImageObject, PageObjects, TextBlock

def read_pdf(path: Path) -> list[PageObjects]:
    doc = fitz.open(path)
    pages = []
    for page_number, page in enumerate(doc, 1):
        blocks = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                text = "".join(span.get("text", "") for span in line["spans"]).strip()
                if not text:
                    continue
                span = line["spans"][0]
                font = span.get("font", "")
                blocks.append(TextBlock(text, tuple(line["bbox"]), span.get("size", 0), font, "bold" in font.lower()))
        images = []
        for image in page.get_images(full=True):
            xref = image[0]
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            info = doc.extract_image(xref)
            images.append(ImageObject(xref, tuple(rects[0]), info["image"], info["ext"]))
        images.sort(key=lambda image: (round(image.bbox[1], 1), round(image.bbox[0], 1)))
        pages.append(PageObjects(page_number, page.rect.width, page.rect.height, blocks, images))
    doc.close()
    return pages

