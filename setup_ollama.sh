#!/usr/bin/env bash
set -euo pipefail

MODEL="${PIN_OLLAMA_MODEL:-qwen2.5vl:3b}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is required for optional vision verification." >&2
  echo "Install it from https://ollama.com/download, then run this script again." >&2
  exit 1
fi

ollama pull "$MODEL"
echo "Installed local vision model: $MODEL."
