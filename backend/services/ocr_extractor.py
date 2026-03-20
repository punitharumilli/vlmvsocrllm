"""
OCR + LLM Extraction Path:
    1. Parse document with Docling (OCR/layout-aware conversion)
    2. Export extracted text
    3. Send raw text to Gemini for structured extraction
"""

import json
import os
import tempfile
import time
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

from google import genai
from google.genai import types

from services.schema import RESPONSE_SCHEMA
from services.vlm_extractor import VLM_SYSTEM_INSTRUCTION


def _doc_to_text(doc_bytes: bytes, filename: str) -> str:
    """Extract text from a PDF/image document using Docling."""
    suffix = Path(filename).suffix.lower() or ".pdf"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(doc_bytes)
        tmp_path = Path(tmp.name)

    try:
        pipeline_opts = PdfPipelineOptions()
        pipeline_opts.accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice.CPU
        )
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts),
                InputFormat.IMAGE: PdfFormatOption(pipeline_options=pipeline_opts),
            }
        )
        conversion_result = converter.convert(tmp_path)
        text = conversion_result.document.export_to_markdown().strip()
        if not text:
            raise ValueError("Docling returned empty text output.")
        return text
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)


def extract_ocr_llm(doc_bytes: bytes, api_key: str, filename: str = "document.pdf") -> dict:
    """
    OCR the PDF then send the raw text to Gemini for extraction.
    Returns {"result": ..., "time_ms": ..., "ocr_text": ..., "input_tokens": ..., "output_tokens": ...}.
    """
    start = time.perf_counter()

    # Step 1 – OCR/Text conversion
    ocr_text = _doc_to_text(doc_bytes, filename)

    # Step 2 – Send OCR text to Gemini (same model, schema & instruction)
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                parts=[
                    types.Part.from_text(
                        text=(
                            "Extract from the following OCR text...\n\n" + ocr_text
                        ),
                    ),
                ],
            ),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            system_instruction=VLM_SYSTEM_INSTRUCTION,
            temperature=0,
        ),
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    result = json.loads(response.text)

    # Extract token usage
    usage = response.usage_metadata
    input_tokens = getattr(usage, "prompt_token_count", 0) or 0
    output_tokens = getattr(usage, "candidates_token_count", 0) or 0

    return {
        "result": result,
        "time_ms": round(elapsed_ms, 1),
        "ocr_text": ocr_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
