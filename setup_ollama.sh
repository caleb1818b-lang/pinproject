#!/bin/zsh
set -e

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is required. Install it from https://ollama.com/download, then run this script again."
  exit 1
fi

ollama pull qwen2.5vl:3b
echo "Installed local 4-bit vision model: qwen2.5vl:3b (Q4_K_M)."
