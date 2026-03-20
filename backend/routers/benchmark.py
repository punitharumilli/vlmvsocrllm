"""
Benchmark router – POST /api/benchmark
Runs VLM and OCR+LLM extraction concurrently and returns comparison data.
"""

import asyncio
import os
import traceback

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(tags=["benchmark"])

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


@router.post("/benchmark")
async def run_benchmark(
    file: UploadFile = File(...), master_xml: UploadFile | None = File(None)
):
    """Run both VLM and OCR+LLM extraction on the uploaded PDF."""
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set.",
        )

    filename = file.filename or "document.pdf"
    if not filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".tiff")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and image files are supported.",
        )

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    master_xml_text = ""
    if master_xml:
        master_name = (master_xml.filename or "master.xml").lower()
        if not master_name.endswith(".xml"):
            raise HTTPException(status_code=400, detail="Master file must be an XML file.")
        master_bytes = await master_xml.read()
        if not master_bytes:
            raise HTTPException(status_code=400, detail="Uploaded master XML is empty.")
        master_xml_text = master_bytes.decode("utf-8", errors="replace")

    # Lazy-import heavy services to keep module import fast
    from services.vlm_extractor import extract_vlm
    from services.ocr_extractor import extract_ocr_llm
    from services.drmd_xml import compare_with_master, generate_drmd_xml

    # Run both paths concurrently in separate threads
    vlm_future = asyncio.to_thread(extract_vlm, pdf_bytes, GEMINI_API_KEY)
    ocr_future = asyncio.to_thread(
        extract_ocr_llm, pdf_bytes, GEMINI_API_KEY, filename
    )

    vlm_raw, ocr_raw = await asyncio.gather(
        vlm_future, ocr_future, return_exceptions=True
    )

    # Build response, handling per-path errors independently
    response: dict = {}

    if isinstance(vlm_raw, Exception):
        response["vlm_result"] = None
        response["vlm_xml"] = ""
        response["vlm_time_ms"] = 0
        response["vlm_input_tokens"] = 0
        response["vlm_output_tokens"] = 0
        response["vlm_error"] = f"{type(vlm_raw).__name__}: {vlm_raw}"
        traceback.print_exception(type(vlm_raw), vlm_raw, vlm_raw.__traceback__)
    else:
        response["vlm_result"] = vlm_raw["result"]
        response["vlm_xml"] = generate_drmd_xml(vlm_raw["result"])
        response["vlm_time_ms"] = vlm_raw["time_ms"]
        response["vlm_input_tokens"] = vlm_raw.get("input_tokens", 0)
        response["vlm_output_tokens"] = vlm_raw.get("output_tokens", 0)

    if isinstance(ocr_raw, Exception):
        response["ocr_llm_result"] = None
        response["ocr_llm_xml"] = ""
        response["ocr_llm_time_ms"] = 0
        response["ocr_input_tokens"] = 0
        response["ocr_output_tokens"] = 0
        response["ocr_raw_text"] = ""
        response["ocr_llm_error"] = f"{type(ocr_raw).__name__}: {ocr_raw}"
        traceback.print_exception(type(ocr_raw), ocr_raw, ocr_raw.__traceback__)
    else:
        response["ocr_llm_result"] = ocr_raw["result"]
        response["ocr_llm_xml"] = generate_drmd_xml(ocr_raw["result"])
        response["ocr_llm_time_ms"] = ocr_raw["time_ms"]
        response["ocr_input_tokens"] = ocr_raw.get("input_tokens", 0)
        response["ocr_output_tokens"] = ocr_raw.get("output_tokens", 0)
        response["ocr_raw_text"] = ocr_raw["ocr_text"]

    response["master_xml_uploaded"] = bool(master_xml_text)
    response["master_xml_score"] = None
    if master_xml_text:
        score: dict = {}
        if response.get("vlm_xml"):
            try:
                score["vlm"] = compare_with_master(response["vlm_xml"], master_xml_text)
            except Exception as exc:
                score["vlm_error"] = f"{type(exc).__name__}: {exc}"
        if response.get("ocr_llm_xml"):
            try:
                score["ocr_llm"] = compare_with_master(
                    response["ocr_llm_xml"], master_xml_text
                )
            except Exception as exc:
                score["ocr_llm_error"] = f"{type(exc).__name__}: {exc}"
        response["master_xml_score"] = score

    return JSONResponse(content=response)


@router.post("/compare-master")
async def compare_master_xml(
    master_xml: UploadFile = File(...),
    vlm_xml: str = Form(""),
    ocr_llm_xml: str = Form(""),
):
    """Compare existing VLM/OCR XML outputs against an uploaded master XML."""
    master_name = (master_xml.filename or "master.xml").lower()
    if not master_name.endswith(".xml"):
        raise HTTPException(status_code=400, detail="Master file must be an XML file.")

    master_bytes = await master_xml.read()
    if not master_bytes:
        raise HTTPException(status_code=400, detail="Uploaded master XML is empty.")

    if not vlm_xml and not ocr_llm_xml:
        raise HTTPException(
            status_code=400,
            detail="At least one extracted XML (vlm_xml or ocr_llm_xml) is required.",
        )

    master_xml_text = master_bytes.decode("utf-8", errors="replace")

    from services.drmd_xml import compare_with_master

    score: dict = {}
    if vlm_xml:
        try:
            score["vlm"] = compare_with_master(vlm_xml, master_xml_text)
        except Exception as exc:
            score["vlm_error"] = f"{type(exc).__name__}: {exc}"

    if ocr_llm_xml:
        try:
            score["ocr_llm"] = compare_with_master(ocr_llm_xml, master_xml_text)
        except Exception as exc:
            score["ocr_llm_error"] = f"{type(exc).__name__}: {exc}"

    return JSONResponse(content={"master_xml_score": score})
