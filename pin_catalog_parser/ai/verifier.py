"""Optional local Qwen verifier seam for ambiguous products."""
import json
from pathlib import Path
from ..models import Product
from .prompts import PRODUCT_VERIFICATION

def should_verify(product: Product, threshold: float = 0.90) -> bool:
    return product.confidence < threshold

def verify(product: Product, model=None) -> Product:
    """Run a local model adapter if supplied; never sends data to a cloud API."""
    if model is None:
        return product
    result = model(PRODUCT_VERIFICATION, product.image_path)
    data = json.loads(result) if isinstance(result, str) else result
    product.item = data.get("Item", product.item)
    product.price = data.get("Price", product.price)
    product.notes = data.get("Notes", product.notes)
    product.collection = data.get("Collection", product.collection)
    product.confidence = max(product.confidence, 0.90)
    return product

def load_qwen_4bit(model_dir: Path):
    """Load Qwen2.5-VL locally when optional transformers/torch are installed."""
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_dir, torch_dtype="auto", device_map="auto", load_in_4bit=True)
    processor = AutoProcessor.from_pretrained(model_dir)
    return model, processor
