from pathlib import Path
from ..models import PageObjects

def extract_images(pages: list[PageObjects], output_dir: Path) -> None:
    from PIL import Image
    from io import BytesIO
    output_dir.mkdir(parents=True, exist_ok=True)
    for page in pages:
        for index, image in enumerate(page.images, 1):
            target = output_dir / f"page-{page.number:03d}-image-{index:02d}.png"
            try:
                source = Image.open(BytesIO(image.data))
                if source.mode not in ("RGB", "RGBA"):
                    source = source.convert("RGBA")
                source.save(target, format="PNG")
                image.image_path = target
            except Exception:
                # Keep unusual embedded artwork available; the exporter can still skip it.
                fallback = target.with_suffix(f".{image.ext}")
                fallback.write_bytes(image.data)
                image.image_path = fallback
