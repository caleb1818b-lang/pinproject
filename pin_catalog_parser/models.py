from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class TextBlock:
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float = 0.0
    font_name: str = ""
    bold: bool = False

@dataclass
class PageObjects:
    number: int
    width: float
    height: float
    text_blocks: list[TextBlock] = field(default_factory=list)
    images: list["ImageObject"] = field(default_factory=list)

@dataclass
class ImageObject:
    xref: int
    bbox: tuple[float, float, float, float]
    data: bytes = b""
    ext: str = "png"
    image_path: Optional[Path] = None

@dataclass
class Product:
    store: str = ""
    date: str = ""
    collection: str = ""
    item: str = ""
    price: str = ""
    notes: str = ""
    image_path: Optional[Path] = None
    confidence: float = 0.0

