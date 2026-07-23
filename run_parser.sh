#!/usr/bin/env bash
set -euo pipefail

SCRIPT_SOURCE="${BASH_SOURCE[0]:-$0}"
PROJECT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd)"
VENV_DIR="$(mktemp -d -t pinproject-venv.XXXXXX)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
INPUT_PATH="${1:-$PROJECT_DIR/catalog-pdfs}"
if [[ $# -gt 0 ]]; then
  shift
fi
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/output}"

cleanup() {
  rm -rf "$VENV_DIR"
}
trap cleanup EXIT INT TERM

if [[ "${PIN_USE_OLLAMA:-0}" == "1" ]] && ! command -v ollama >/dev/null 2>&1; then
  echo "PIN_USE_OLLAMA=1 was requested, but Ollama is not installed or not on PATH." >&2
  echo "Install Ollama or run without PIN_USE_OLLAMA for the fast deterministic parser." >&2
  exit 1
fi

"$PYTHON_BIN" -m venv --system-site-packages "$VENV_DIR"
"$VENV_DIR/bin/python" - <<'PY' || "$VENV_DIR/bin/python" -m pip install --quiet -r "$PROJECT_DIR/requirements.txt"
import fitz
import openpyxl
import PIL
import json_repair
PY
PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$VENV_DIR/bin/python" -m pin_catalog_parser.main \
  "$INPUT_PATH" \
  --output "$OUTPUT_DIR" \
  "$@"

echo "Finished. Combined workbook is in: $OUTPUT_DIR/disney-pin-catalogue.xlsx"
echo "Temporary Python environment removed."
