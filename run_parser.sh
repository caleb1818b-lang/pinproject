#!/bin/zsh
set -e

PROJECT_DIR="${0:A:h}"
VENV_DIR="$(mktemp -d -t pinproject-venv)"

cleanup() {
  rm -rf "$VENV_DIR"
}
trap cleanup EXIT INT TERM

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is required. Install it from https://ollama.com/download, then run ~/Documents/pinproject/setup_ollama.sh"
  exit 1
fi

"$(command -v python3)" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
"$VENV_DIR/bin/python" -m pip install --quiet "$PROJECT_DIR"
"$VENV_DIR/bin/python" -m pin_catalog_parser.main \
  "$PROJECT_DIR/catalog-pdfs" \
  --output "$PROJECT_DIR/output"

echo "Finished. Temporary Python environment removed."
