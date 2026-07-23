# Disney Pin Catalog Parser — Phase 1 MVP

## Where to put your catalog PDFs

Create a folder named `catalog-pdfs` next to the `pin_catalog_parser` folder, then place the PDF files you want processed inside it:

```text
project-folder/
├── catalog-pdfs/
│   ├── disney-pins-january-2026.pdf
│   └── disney-pins-february-2026.pdf
└── pin_catalog_parser/
```

You can use any PDF filenames, including spaces, punctuation, and uppercase `.PDF` extensions. The program processes every PDF directly inside `catalog-pdfs` and ignores unrelated files.

## Run the parser

After moving the complete project folder to `~/Documents/pinproject`, open Terminal and make the helper executable once:

```bash
cd ~/Documents/pinproject
chmod +x run_parser.sh
chmod +x setup_ollama.sh
~/Documents/pinproject/setup_ollama.sh
```

This installs the local `qwen2.5vl:3b` vision model. Ollama reports this tag as `Q4_K_M`, a 4-bit quantization. Ollama manages the underlying GGUF data in its own model store; do not manually move or rename a `.gguf` file.

Run the parser with:

```bash
~/Documents/pinproject/run_parser.sh
```

The helper creates a temporary virtual environment, installs the project dependencies (including Pillow for embedded Excel images), processes every PDF in `catalog-pdfs`, writes Excel files to `output`, and removes the temporary environment when finished. Press `Ctrl-C` to cancel; cleanup also runs then. A forced kill (`kill -9`) cannot run cleanup, so remove any leftover temporary folder beginning with `/tmp/pinproject-venv` if that rare case occurs.

After it finishes, the `output` folder will contain one combined Excel file for all PDFs:

```text
output/
├── disney-pin-catalogue.xlsx
├── disney-pins-january-2026/
│   └── images/
└── disney-pins-february-2026/
    └── images/
```

The combined Excel file contains embedded images and the columns `Store`, `Date`, `Collection`, `Item`, `Price`, `Notes`, and `Image`. Empty/unusable product rows are omitted. The source PDF filename is included in `Notes`.

The first page is treated as catalog metadata/cover material, so headings such as `PIN PRODUCT CATALOG` and publication dates are not exported as products. Product pages are grouped by image and nearby text; individual pins remain separate rows even when they share a collection.

Vision verification is designed as a local-only optional step for low-confidence rows. The adapter supports a local Qwen2.5-VL 3B 4-bit model directory; no cloud service is used. The deterministic parser remains the default until a model directory is configured and tested against your catalogs.

To process a single file instead, run:

```bash
python3 -m pin_catalog_parser.main ~/Documents/pinproject/catalog-pdfs/disney-pins-january-2026.pdf --output ~/Documents/pinproject/output
```

The first pass is deterministic: PyMuPDF extracts text, font metadata, coordinates, and embedded images; the relationship builder associates each image with nearby text. The confidence field is retained in the model for the Phase 1.1 local Qwen verifier. A future macOS app can call `process()` directly from a Swift/PyObjC shell or package this Python runtime with PyInstaller.
