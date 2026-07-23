# Disney Pin Catalog Parser

Convert Disney pin catalog PDFs into one Excel workbook with product rows and embedded images.

## Inputs and outputs

Put PDFs in `catalog-pdfs` next to the Python package:

```text
pinproject/
├── catalog-pdfs/
│   ├── disney-pins-january-2026.pdf
│   └── disney-pins-february-2026.pdf
├── output/
└── pin_catalog_parser/
```

The parser processes every PDF directly inside `catalog-pdfs` and writes:

```text
output/disney-pin-catalogue.xlsx
```

The workbook includes `Store`, `Date`, `Collection`, `Item`, `Price`, `Notes`, and `Image` columns. Empty/unusable rows are skipped, and the source PDF filename is included in the `Notes` column.

## Fast local run (macOS, Linux, or Colab)

The default path is the fast deterministic parser. It does **not** require Ollama and is the recommended first run.

```bash
cd /path/to/pinproject
chmod +x run_parser.sh
./run_parser.sh
```

You can pass a single PDF or a different folder:

```bash
./run_parser.sh /path/to/catalog-or-pdf
```

You can also run the module directly:

```bash
python3 -m pip install -e .
python3 -m pin_catalog_parser.main catalog-pdfs --output output
```

## Optional GPU/Ollama vision mode

Vision mode can improve difficult pages, but it is slower and requires Ollama plus a vision model. Use it only when you have GPU resources available, such as a Google Colab GPU runtime or a local NVIDIA/Mac GPU setup supported by Ollama.

```bash
cd /path/to/pinproject
chmod +x setup_ollama.sh run_parser.sh
./setup_ollama.sh
PIN_USE_OLLAMA=1 ./run_parser.sh
```

By default this uses `qwen2.5vl:3b`. Override it with:

```bash
PIN_OLLAMA_MODEL=qwen2.5vl:3b PIN_USE_OLLAMA=1 ./run_parser.sh
```

## Google Colab GPU notebook

Open `notebooks/pinproject_colab_gpu_runner.ipynb` in Google Colab. The notebook:

1. Lets you set the public GitHub repo URL and branch.
2. Clones the repo into `/content/pinproject`.
3. Installs this package.
4. Mounts Google Drive when `SAVE_TO_GOOGLE_DRIVE = True`.
5. Optionally installs and starts Ollama for GPU vision mode.
6. Runs the existing `run_parser.sh` helper.
7. Saves the workbook to `DRIVE_OUTPUT_DIR` (default `/content/drive/MyDrive/pinproject-output`).
8. Downloads `disney-pin-catalogue.xlsx` as a convenience copy.

For the fastest reliable run, leave `USE_OLLAMA_VISION = False`. Turn it on only after selecting **Runtime → Change runtime type → GPU** in Colab. Keep `SAVE_TO_GOOGLE_DRIVE = True` if you want the spreadsheet preserved after the Colab runtime disconnects.

## Development notes

- `run_parser.sh` is Bash-compatible and no longer depends on macOS-only zsh path expansion.
- `setup_ollama.sh` is optional; the repository works without Ollama in deterministic mode.
- The first page is treated as metadata/cover material and is not exported as products.
- Product pages are grouped by image and nearby text in deterministic mode, or by overlapping rendered page tiles in Ollama vision mode.

## Spreadsheet correctness

The deterministic parser now reads item names and prices from the page text, treats large page headings as collections, supports pages with multiple collection prefixes such as `FIRE ELEMENT - Character Name`, and keeps each product linked to the nearest extracted page image instead of cycling through images after parsing.
