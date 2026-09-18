"""
FastAPI Backend for Level 2 RFP Evaluation Pipeline
----------------------------------------------------
Provides REST API endpoints for:
1. Stage 1: Extract criteria from RFP (`POST /api/extract-criteria`).
2. Stage 2: Evaluate vendor response with user-adapted criteria (`POST /api/feedback`).
3. Unified: Full end-to-end evaluation (`POST /api/evaluate`).
4. Sample Demo: Instant sample criteria and evaluations (`GET /api/sample`, `GET /api/sample/criteria`).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Import pipeline stages with flexible fallback
try:
    from pipeline import (
        extract_criteria_stage,
        evaluate_response_stage,
        lvl2_pipeline,
        adapt_criteria_descriptions,
    )
except ImportError:
    try:
        from .pipeline import (
            extract_criteria_stage,
            evaluate_response_stage,
            lvl2_pipeline,
            adapt_criteria_descriptions,
        )
    except ImportError:
        from backend.pipeline import (
            extract_criteria_stage,
            evaluate_response_stage,
            lvl2_pipeline,
            adapt_criteria_descriptions,
        )


# ---------------------------------------------------------------------
# Session Artifact Hygiene & Purge Functionality
# ---------------------------------------------------------------------
def purge_stale_session_artifacts() -> Dict[str, Any]:
    """
    Scans and permanently removes all ephemeral evaluation artifacts:
    - response_feedback_*.json
    - response_correction_*.json
    - Temporary directories (/tmp/rfp_eval_*, /tmp/crit_eval_*, /tmp/rfp_crit_*)
    - custom_criteria_*.json
    - Any intermediate files left from prior runs.
    Ensures that outside an active session, no evaluation data is retained on disk.
    """
    purged_items = []
    search_dirs = [
        Path("/app"),
        Path.cwd(),
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent / "trash",
        Path(tempfile.gettempdir())
    ]

    cleanup_patterns = [
        "response_feedback_*.json",
        "response_correction_*.json",
        "custom_criteria*.json",
        "extracted_criteria*.json",
        "evaluation_result*.json",
        "rfp_eval_*",
        "crit_eval_*",
        "rfp_crit_*"
    ]

    for s_dir in search_dirs:
        if not s_dir.exists() or not s_dir.is_dir():
            continue
        for pat in cleanup_patterns:
            try:
                for entry in s_dir.glob(pat):
                    try:
                        if entry.is_file():
                            entry.unlink(missing_ok=True)
                            purged_items.append(str(entry.name))
                        elif entry.is_dir():
                            shutil.rmtree(entry, ignore_errors=True)
                            purged_items.append(str(entry.name))
                    except Exception:
                        pass
            except Exception:
                pass

    return {
        "status": "clean",
        "purged_count": len(purged_items),
        "purged_items": purged_items
    }

# Initialize FastAPI application
app = FastAPI(
    title="RFP Evaluation & Feedback Pipeline API",
    description="2-Stage interactive API for extracting RFP criteria, customizing priorities (1-5), and evaluating vendor proposals using Google Gemini",
    version="2.0.0",
)

# ---------------------------------------------------------------------
# CORS Middleware Configuration
# ---------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper: Discover files across container and local environments
def _find_file(rel_paths: list[str]) -> Optional[Path]:
    search_roots = [
        Path("/app"),
        Path(__file__).resolve().parent.parent,
        Path(__file__).resolve().parent,
        Path.cwd(),
    ]
    for root in search_roots:
        for rel in rel_paths:
            candidate = root / rel
            if candidate.is_file():
                return candidate
    return None


def _find_frontend_dir() -> Optional[Path]:
    search_roots = [
        Path("/app/frontend"),
        Path(__file__).resolve().parent.parent / "frontend",
        Path.cwd() / "frontend",
    ]
    for d in search_roots:
        if d.is_dir() and (d / "index.html").is_file():
            return d
    return None


FRONTEND_DIR = _find_frontend_dir()


# ---------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------
@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint to verify backend status."""
    return {"status": "healthy", "service": "RFP Evaluation Pipeline", "version": "2.0.0"}



# ---------------------------------------------------------------------
# Session Management & Presets Endpoints
# ---------------------------------------------------------------------
@app.on_event("startup")
async def startup_session_cleanup():
    """Verify and purge any leftover artifacts from prior runs when backend boots."""
    res = purge_stale_session_artifacts()
    print(f"[Session Startup Cleanup] Purged {res['purged_count']} lingering artifacts.")


@app.post("/api/session/reset")
@app.post("/api/session/purge")
async def reset_session_endpoint() -> Dict[str, Any]:
    """
    Explicitly wipes all ephemeral evaluation files, criteria, feedback, and corrections
    from the server to guarantee a completely clean, isolated session.
    """
    res = purge_stale_session_artifacts()
    return {
        "status": "success",
        "message": "Session reset complete. All prior criteria, feedback, and corrections purged.",
        "details": res
    }


PRESET_CONFIGS = {
    "weak": {
        "vendor": "BrightPath Software Solutions",
        "variant": "Weak (Generic / Missing Key Requirements)",
        "rfp_rel": ["data/sample_data/rfp_nordframe.md", "sample_data/rfp_nordframe.md", "rfp_nordframe.md"],
        "resp_rel": ["data/response/response_1_weak.md", "response/response_1_weak.md", "response_1_weak.md"],
        "rfp_name": "rfp_nordframe.md",
        "resp_name": "response_1_weak.md",
    },
    "medium": {
        "vendor": "Clarion Data Systems",
        "variant": "Medium (Baseline Compliance)",
        "rfp_rel": ["data/sample_data/rfp_nordframe.md", "sample_data/rfp_nordframe.md", "rfp_nordframe.md"],
        "resp_rel": ["data/response/response_2_medium.md", "response/response_2_medium.md", "response_2_medium.md"],
        "rfp_name": "rfp_nordframe.md",
        "resp_name": "response_2_medium.md",
    },
    "strong": {
        "vendor": "Apex Supply Chain Tech",
        "variant": "Strong (High Compliance)",
        "rfp_rel": ["data/sample_data/rfp_nordframe.md", "sample_data/rfp_nordframe.md", "rfp_nordframe.md"],
        "resp_rel": ["data/response/response_3_strong.md", "response/response_3_strong.md", "response_3_strong.md"],
        "rfp_name": "rfp_nordframe.md",
        "resp_name": "response_3_strong.md",
    },
    "overpromise": {
        "vendor": "Vantix AI Solutions",
        "variant": "Overpromising (High Implementation Risk)",
        "rfp_rel": ["data/sample_data/rfp_nordframe.md", "sample_data/rfp_nordframe.md", "rfp_nordframe.md"],
        "resp_rel": ["data/response/response_4_overpromise.md", "response/response_4_overpromise.md", "response_4_overpromise.md"],
        "rfp_name": "rfp_nordframe.md",
        "resp_name": "response_4_overpromise.md",
    },
}


@app.get("/api/presets/{preset_key}")
async def get_preset_scenario(preset_key: str) -> Dict[str, Any]:
    """
    Returns the raw file text for benchmark RFP and vendor proposal files.
    This enables the client to load authentic documents and perform fresh AI evaluation
    without relying on static pre-cooked results.
    """
    key = preset_key.lower().strip()
    cfg = PRESET_CONFIGS.get(key)
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown preset scenario '{preset_key}'. Available: {list(PRESET_CONFIGS.keys())}"
        )

    rfp_path = _find_file(cfg["rfp_rel"])
    resp_path = _find_file(cfg["resp_rel"])

    if not rfp_path or not rfp_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RFP file for preset '{preset_key}' could not be located."
        )

    if not resp_path or not resp_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response file for preset '{preset_key}' could not be located."
        )

    with open(rfp_path, "r", encoding="utf-8") as f:
        rfp_text = f.read()

    with open(resp_path, "r", encoding="utf-8") as f:
        resp_text = f.read()

    return {
        "preset_key": key,
        "vendor_name": cfg["vendor"],
        "variant": cfg["variant"],
        "rfp_filename": cfg["rfp_name"],
        "rfp_content": rfp_text,
        "response_filename": cfg["resp_name"],
        "response_content": resp_text
    }

@app.get("/api/sample/criteria")
async def get_sample_criteria() -> Dict[str, Any]:
    """Return pre-computed sample criteria for instant Stage 1 UI demo."""
    sample_crit = _find_file([
        "data/samples/criteria.json",
        "criteria.json",
        "data/samples/criterias_output.json",
        "criterias_output.json"
    ])
    if sample_crit:
        with open(sample_crit, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Sample criteria file 'criteria.json' not found."
    )


@app.get("/api/sample")
async def get_sample_result() -> Dict[str, Any]:
    """Return pre-computed sample evaluation result for instant full UI demo."""
    sample_path = _find_file([
        "data/samples/lvl2_pipeline_output_response_2_medium.json",
        "lvl2_pipeline_output_response_2_medium.json"
    ])
    if sample_path:
        with open(sample_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Sample result file not found."
    )


# =====================================================================

# =====================================================================
# ADAPT CRITERIA DESCRIPTIONS (LITE MODEL)
# =====================================================================
@app.post("/api/criteria/adapt-descriptions")
@app.post("/api/criteria/rephrase")
async def adapt_criteria_endpoint(
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """
    Regenerates requirement descriptions and rationales with LITE_MODEL
    to reflect modified priority marks (1 to 5) before response evaluation.
    Updates the criteria report in-place and returns it to the client.
    """
    criteria_report = payload.get("criteria_report") or payload
    if not isinstance(criteria_report, dict) or "criteria" not in criteria_report:
        if isinstance(criteria_report, list):
            criteria_report = {"criteria": criteria_report, "total_criteria": len(criteria_report)}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid criteria payload. Must contain 'criteria' list."
            )

    only_modified = payload.get("only_modified", True)

    try:
        updated_report = adapt_criteria_descriptions(
            criteria_data=criteria_report,
            only_modified=only_modified,
        )
        return JSONResponse(content={
            "status": "success",
            "criteria_report": updated_report,
            "message": "Criteria descriptions successfully adapted to priority marks."
        })
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to adapt criteria descriptions: {str(err)}"
        )

# STAGE 1: Extract Criteria from RFP
# =====================================================================
@app.post("/api/extract-criteria")
@app.post("/api/criteria/extract")
async def extract_criteria_endpoint(
    rfp_file: UploadFile = File(..., description="Customer RFP document (.md, .txt)"),
) -> Dict[str, Any]:
    """
    Stage 1: Extracts requirements and assigns 1-5 priority ratings from an RFP.
    Returns criteria dictionary for user review and customization before response evaluation.
    """
    if not rfp_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing RFP file or invalid filename.",
        )

    # Hygiene check: verify & purge prior ephemeral artifacts before starting new extraction
    purge_stale_session_artifacts()

    temp_dir = tempfile.mkdtemp(prefix="rfp_crit_")
    try:
        rfp_dest = Path(temp_dir) / rfp_file.filename
        with open(rfp_dest, "wb") as f_out:
            shutil.copyfileobj(rfp_file.file, f_out)

        if rfp_dest.stat().st_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Uploaded RFP file '{rfp_file.filename}' is empty.",
            )

        criteria_output_path = Path(temp_dir) / "extracted_criteria.json"

        try:
            criteria_report = extract_criteria_stage(
                rfp_file=str(rfp_dest),
                output_file=str(criteria_output_path),
            )
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Criteria extraction failed: {str(err)}",
            )

        return JSONResponse(content={
            "status": "success",
            "criteria_report": criteria_report,
        })

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =====================================================================
# STAGE 2: Evaluate Response with User-Customized Criteria
# =====================================================================
@app.post("/api/feedback")
@app.post("/api/evaluate-response")
async def evaluate_feedback_endpoint(
    response_file: UploadFile = File(..., description="Vendor proposal document (.md, .txt)"),
    criteria_data: Optional[str] = Form(None, description="JSON string of user-customized criteria report"),
    criteria_json: Optional[str] = Form(None, description="Alternative field name for criteria report JSON"),
    rfp_file: Optional[UploadFile] = File(None, description="Optional Customer RFP document"),
) -> Dict[str, Any]:
    """
    Stage 2: Evaluates a vendor response against user-customized criteria.
    Accepts the proposal document and the updated criteria JSON payload.
    """
    if not response_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Response file or invalid filename.",
        )

    raw_criteria = criteria_data or criteria_json
    if not raw_criteria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing criteria payload: please provide 'criteria_data' or 'criteria_json'.",
        )

    # Hygiene check: verify & purge prior ephemeral artifacts before starting new evaluation
    purge_stale_session_artifacts()

    # Validate criteria JSON
    try:
        parsed_criteria = json.loads(raw_criteria)
    except Exception as json_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid criteria JSON: {str(json_err)}",
        )

    if isinstance(parsed_criteria, dict) and "criteria_report" in parsed_criteria and isinstance(parsed_criteria["criteria_report"], dict):
        parsed_criteria = parsed_criteria["criteria_report"]
    elif isinstance(parsed_criteria, list):
        parsed_criteria = {"criteria": parsed_criteria, "total_criteria": len(parsed_criteria)}

    if not isinstance(parsed_criteria, dict) or "criteria" not in parsed_criteria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="criteria_data must contain a 'criteria' array.",
        )

    temp_dir = tempfile.mkdtemp(prefix="rfp_eval_")
    try:
        response_dest = Path(temp_dir) / response_file.filename
        with open(response_dest, "wb") as f_out:
            shutil.copyfileobj(response_file.file, f_out)

        if response_dest.stat().st_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Uploaded Response file '{response_file.filename}' is empty.",
            )

        output_json_path = Path(temp_dir) / "evaluation_result.json"

        try:
            result = evaluate_response_stage(
                criteria_input=parsed_criteria,
                response_file=str(response_dest),
                output_file=str(output_json_path),
            )
        except Exception as eval_err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Evaluation failed: {str(eval_err)}",
            )

        return JSONResponse(content=result)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Completely purge all ephemeral evaluation artifacts when session/request ends
        purge_stale_session_artifacts()


# =====================================================================
# UNIFIED PIPELINE (Backward Compatibility)
# =====================================================================
@app.post("/api/evaluate")
async def evaluate_proposal_unified(
    rfp_file: UploadFile = File(..., description="Customer RFP document (.md, .txt)"),
    response_file: UploadFile = File(..., description="Vendor proposal document (.md, .txt)"),
) -> Dict[str, Any]:
    """
    Unified end-to-end evaluation: accepts both RFP and Response,
    runs full pipeline, and returns consolidated JSON.
    """
    if not rfp_file.filename or not response_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both rfp_file and response_file are required.",
        )

    temp_dir = tempfile.mkdtemp(prefix="rfp_unified_")
    try:
        rfp_dest = Path(temp_dir) / rfp_file.filename
        response_dest = Path(temp_dir) / response_file.filename

        with open(rfp_dest, "wb") as f_out:
            shutil.copyfileobj(rfp_file.file, f_out)
        with open(response_dest, "wb") as f_out:
            shutil.copyfileobj(response_file.file, f_out)

        output_json_path = Path(temp_dir) / "pipeline_result.json"

        try:
            result = lvl2_pipeline(
                rfp_file=str(rfp_dest),
                response_file=str(response_dest),
                output_file=str(output_json_path),
            )
        except Exception as pipeline_err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pipeline processing failed: {str(pipeline_err)}",
            )

        return JSONResponse(content=result)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Completely purge all ephemeral evaluation artifacts when session/request ends
        purge_stale_session_artifacts()


# ---------------------------------------------------------------------
# Serve Frontend Static Assets
# ---------------------------------------------------------------------
if FRONTEND_DIR:
    @app.get("/")
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend index.html not found"}

    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
