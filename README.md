# VLM vs OCR+LLM DRMD Benchmark

Benchmark application to compare two extraction strategies for Reference Material Certificates:

- `VLM path`: send source document directly to Gemini Vision
- `OCR+LLM path`: parse document text with Docling, then extract structured data with Gemini

Both paths produce DRMD-style XML, and both can be compared against a master XML ground truth.

## What This Project Does

- Runs VLM and OCR+LLM extraction concurrently on the same input file
- Generates DRMD JSON and DRMD XML outputs for each path
- Lets you upload a master XML after extraction and score both methods
- Shows side-by-side and diff views
- Exports downloadable HTML/Markdown reports
- Computes top-level winners for:
  - extraction quality (against master XML)
  - speed
  - token efficiency

## Why Docling Instead of Tesseract OCR

Short answer: our target is structured certificate understanding (tables, reading order, sections, and XML field mapping), not only line-level OCR text.

### Research-backed rationale

1. Document AI research shows layout + vision context is essential.
- LayoutLM (KDD 2020) shows that jointly modeling text and layout significantly improves document understanding tasks such as form and receipt extraction.
- Paper: `https://arxiv.org/abs/1912.13318`

2. Newer multimodal models continue this result.
- LayoutLMv3 reports state-of-the-art performance across text-centric and image-centric document tasks using unified text-image pretraining.
- Paper: `https://arxiv.org/abs/2204.08387`

3. OCR-first pipelines have known limitations.
- Donut (ECCV 2022) explicitly identifies OCR pipeline drawbacks: OCR compute overhead, limited flexibility across domains/languages, and OCR error propagation into downstream extraction.
- Paper: `https://arxiv.org/abs/2111.15664`

4. Table structure matters for scientific/certificate data.
- OTSL table-structure work (ICDAR 2023) shows that table representation strongly affects accuracy and runtime in document pipelines.
- Paper: `https://arxiv.org/abs/2305.03393`

5. Docling is designed as a full document-conversion stack.
- Docling Technical Report describes a self-contained conversion package using specialized models for layout analysis and table structure recognition, with efficient execution on commodity hardware.
- Paper: `https://arxiv.org/abs/2408.09869`
- Project: `https://github.com/docling-project/docling`

### Where Tesseract fits

- Tesseract is excellent as a traditional OCR engine and remains a strong choice when you only need text extraction from images.
- Official scope: OCR engine (`libtesseract` + CLI), with outputs such as text/hOCR/TSV/PDF.
- Sources:
  - `https://github.com/tesseract-ocr/tesseract`
  - `https://research.google/pubs/an-overview-of-the-tesseract-ocr-engine/`
  - `https://tesseract-ocr.github.io/tessdoc/`

### Practical reason in this repo

- We benchmark XML extraction quality against a master DRMD XML.
- This requires preserving structure and semantics, not only OCR text.
- Docling gives better upstream document structure for the downstream LLM extraction stage.
- In this implementation, Docling runs in CPU mode for stability on low-VRAM machines.

## Repository Structure

- `backend/`
  - FastAPI API (`/api/benchmark`, `/api/compare-master`)
  - OCR service (`services/ocr_extractor.py`) using Docling
  - VLM service (`services/vlm_extractor.py`)
  - DRMD XML generation + scoring (`services/drmd_xml.py`)
- `frontend/`
  - React + Vite UI
  - Upload, side-by-side, diff, report export
  - Master XML compare flow

## Extraction and Comparison Flow

1. Upload certificate (`pdf/png/jpg/jpeg/tiff`)
2. Backend runs both extraction paths concurrently
3. Each result is converted to DRMD XML
4. Upload master XML using `Master XML Compare`
5. Scoring runs for VLM XML and OCR XML against master XML

## Comparison Normalization Rules

To make scoring fair and stable, comparison ignores or normalizes selected fields:

Ignored fields/paths:
- `uniqueIdentifier` (random)
- `document` payload blocks (binary/base64 payloads)
- `validity/timeAfterDispatch/dispatchDate`
- `mainSigner`

Normalization behavior:
- Unit/value normalization to DSI-compatible forms where mappings exist
- Duration normalization for validity period (`12M -> P1Y`, etc.)
- DRMD title forced to `referenceMaterialCertificate`
- CAS identifiers added automatically for known quantity names/symbols

## API Endpoints

### `POST /api/benchmark`

Request:
- `file`: certificate document

Response includes:
- `vlm_result`, `ocr_llm_result`
- `vlm_xml`, `ocr_llm_xml`
- `vlm_time_ms`, `ocr_llm_time_ms`
- `vlm_input_tokens`, `vlm_output_tokens`
- `ocr_input_tokens`, `ocr_output_tokens`
- `ocr_raw_text`
- per-path error fields if any

### `POST /api/compare-master`

Request:
- `master_xml`: uploaded master XML
- `vlm_xml`: generated VLM XML (form field)
- `ocr_llm_xml`: generated OCR XML (form field)

Response:
- `master_xml_score`
  - `vlm`: `{ total, correct, wrong, accuracy_pct, missing, extra }`
  - `ocr_llm`: same shape

## Local Setup

## Prerequisites

- Python 3.10+
- Node.js 18+
- Gemini API key

## 1) Backend

From repository root:

```bash
cd /home/parumill/Desktop/vlmvsocrllm

# If venv does not exist yet:
python3 -m venv backend/venv

# Install dependencies into venv
./backend/venv/bin/pip install -r backend/requirements.txt

# Set your Gemini key
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Run API
./backend/venv/bin/uvicorn app:app --reload --app-dir backend
```

Health check:

```bash
curl http://localhost:8000/health
```

## 2) Frontend

```bash
cd /home/parumill/Desktop/vlmvsocrllm/frontend
npm install
npm run dev
```

Open:
- `http://localhost:5173`

Vite proxy is already configured to forward `/api` to `http://localhost:8000`.

## Usage Guide

1. Upload certificate in the main upload panel
2. Wait for extraction to complete
3. Click `Master XML Compare` and upload your master XML
4. Review:
- side-by-side view (`Master | VLM | OCR+LLM`)
- diff view (master as baseline)
- top winner stats for quality/speed/tokens
5. Download HTML report (includes highlighted differences similar to diff behavior)

## Report Export

- HTML report includes:
  - winner cards (quality, speed, token efficiency)
  - timing/token summary
  - highlighted differences
  - master-baseline comparison when master XML is provided
- Markdown report includes summarized benchmark and differences

## Notes and Limitations

- OCR+LLM path is CPU-forced for stability on low-VRAM machines.
- Docling dependency stack is heavier than basic OCR-only pipelines.
- Results still depend on source quality and model extraction behavior.
- This tool is for benchmarking and analysis, not strict XML schema validation.


