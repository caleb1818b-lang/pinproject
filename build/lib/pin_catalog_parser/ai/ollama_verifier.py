import base64
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

PROMPT = """Extract exactly one Disney pin product from this image. Return JSON only with these keys: Store, Date, Collection, Item, Price, Notes. Do not invent values. Price must include the dollar sign if visible. The collection is the section heading, not the product name. If a field is not visible, return an empty string."""

PAGE_PROMPT = """Read this catalog page. Return JSON only: {\"products\":[{\"Store\":\"\",\"Date\":\"\",\"Collection\":\"\",\"Item\":\"\",\"Price\":\"\",\"Notes\":\"\"}]}. List every sellable product, including multiple products shown in one image. Ignore logos and headings. Do not invent values."""
TILE_PROMPT = """Read this catalog tile. Return JSON only: {\"products\":[{\"Store\":\"\",\"Date\":\"\",\"Collection\":\"\",\"Item\":\"\",\"Price\":\"\",\"Notes\":\"\"}]}. List every sellable product visible in this tile. Do not omit small products. Ignore partial products cut off at the tile edge; they will be read in an overlapping tile. Do not invent values."""

def parse_json_response(content: str) -> dict:
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json\n", "", 1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            from json_repair import repair_json
            repaired = repair_json(text)
            return json.loads(repaired)
        except Exception:
            pass
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise RuntimeError(f"Ollama returned non-JSON: {text[:300]!r}")

def ollama_status(model: str) -> bool:
    try:
        with urlopen(os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/tags", timeout=5) as response:
            models = json.loads(response.read()).get("models", [])
        available = {entry.get("name") for entry in models}
        if model not in available:
            print(f"  Ollama model not found: {model}. Available: {sorted(available)}")
            return False
        return True
    except Exception as error:
        print(f"  Ollama is not reachable: {error}")
        return False

def verify_image(image_path: Path, context: dict) -> dict:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    prompt = PROMPT + "\nKnown context: " + json.dumps(context, ensure_ascii=False)
    payload = {"model": os.getenv("PIN_OLLAMA_MODEL", "qwen2.5vl:3b"), "stream": False, "options": {"temperature": 0, "num_predict": 300}, "messages": [{"role": "user", "content": prompt, "images": [encoded]}]}
    request = Request(os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=90) as response:
            result = json.loads(response.read())
    except Exception as error:
        detail = getattr(error, "read", lambda: b"")()
        raise RuntimeError(f"Ollama request failed: {detail.decode(errors='replace')[:300] or error}") from error
    return json.loads(result["message"]["content"])

def verify_page(page_path: Path, context: dict) -> list[dict]:
    encoded = base64.b64encode(page_path.read_bytes()).decode("ascii")
    payload = {"model": os.getenv("PIN_OLLAMA_MODEL", "qwen2.5vl:3b"), "stream": False, "keep_alive": "10m", "options": {"temperature": 0, "num_predict": 800, "num_ctx": 8192}, "messages": [{"role": "user", "content": PAGE_PROMPT + "\nKnown context and extracted PDF text: " + json.dumps(context, ensure_ascii=False), "images": [encoded]}]}
    request = Request(os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        timeout = int(os.getenv("PIN_OLLAMA_TIMEOUT", "1800"))
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read())
    except HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"Ollama HTTP {error.code}: {detail[:500]}") from error
    data = parse_json_response(result.get("message", {}).get("content", ""))
    return data.get("products", [])

def verify_tile(tile_path: Path, context: dict) -> list[dict]:
    encoded = base64.b64encode(tile_path.read_bytes()).decode("ascii")
    payload = {"model": os.getenv("PIN_OLLAMA_MODEL", "qwen2.5vl:3b"), "stream": False, "keep_alive": "10m", "options": {"temperature": 0, "num_predict": 350, "num_ctx": 4096}, "messages": [{"role": "user", "content": TILE_PROMPT + "\nKnown context: " + json.dumps(context, ensure_ascii=False), "images": [encoded]}]}
    request = Request(os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=int(os.getenv("PIN_OLLAMA_TIMEOUT", "1800"))) as response:
        result = json.loads(response.read())
    parsed = parse_json_response(result.get("message", {}).get("content", ""))
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        products = parsed.get("products", [])
        return products if isinstance(products, list) else []
    return []
