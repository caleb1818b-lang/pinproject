from ..models import PageObjects, TextBlock

def collection_candidates(page: PageObjects) -> list[TextBlock]:
    sizes = [b.font_size for b in page.text_blocks]
    baseline = sorted(sizes)[int(len(sizes) * .75)] if sizes else 0
    return [b for b in page.text_blocks if b.font_size >= baseline and (b.bold or len(b.text) < 50)]

def nearby_text(page: PageObjects, image_bbox, max_distance=180):
    x0, y0, x1, y1 = image_bbox
    cx = (x0 + x1) / 2
    # Prefer the text directly below this image and stop at the next image's row.
    other_y = sorted(other.bbox[1] for other in page.images if other.bbox != image_bbox and other.bbox[1] > y1)
    next_y = other_y[0] if other_y else page.height
    candidates = [b for b in page.text_blocks if b.bbox[1] >= y1 - 8 and b.bbox[1] < next_y and abs(((b.bbox[0]+b.bbox[2])/2) - cx) < max(90, (x1-x0)*1.5)]
    if not candidates:
        candidates = page.text_blocks
    return sorted(candidates, key=lambda b: abs(b.bbox[1] - y1) + abs((b.bbox[0]+b.bbox[2])/2-cx))
