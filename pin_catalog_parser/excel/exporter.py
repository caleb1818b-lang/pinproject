from pathlib import Path
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from ..models import Product

HEADERS = ["Store", "Date", "Collection", "Item", "Price", "Notes", "Image"]
def safe(value):
    if value is None: return ""
    return ILLEGAL_CHARACTERS_RE.sub("", str(value))

def export(products: list[Product], path: Path) -> None:
    wb, ws = Workbook(), None
    ws = wb.active; ws.title = "Products"; ws.append(HEADERS)
    for row, p in enumerate(products, 2):
        ws.append([safe(p.store), safe(p.date), safe(p.collection), safe(p.item), safe(p.price), safe(p.notes), ""])
        if p.image_path and p.image_path.exists() and p.image_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
            img = XLImage(str(p.image_path)); img.width = 80; img.height = 80
            ws.add_image(img, f"G{row}"); ws.row_dimensions[row].height = 65
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    for col, width in zip("ABCDEFG", [35, 16, 24, 30, 14, 40, 15]): ws.column_dimensions[col].width = width
    wb.save(path)
