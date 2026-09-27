"""
Proposal-Based Analysis API Routes.
Provides active endpoints for proposal document extraction, parameter catalog retrieval,
AI parameter recommendation, and targeted prospect-proposal fit analysis.
"""

import os
import uuid
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from auth.dependencies import get_current_user
from services.proposal_service import build_proposal_profile
from services.proposal_parameter_service import (
    get_parameter_catalog,
    evaluate_all_parameters,
    validate_selected_parameters
)
from services.proposal_analysis_service import (
    analyze_proposal_fit,
    stream_proposal_analysis
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Proposal-Based Analysis"])



class RecommendParametersRequest(BaseModel):
    proposal_profile: Dict[str, Any]


class ProposalAnalyzeRequest(BaseModel):
    prospect_id: Optional[str] = None
    prospect_name: str
    proposal_id: Optional[str] = None
    proposal_profile: Dict[str, Any]
    selected_parameters: List[str]
    mock_mode: Optional[bool] = False


ALLOWED_PROPOSAL_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_PROPOSAL_SIZE = 15 * 1024 * 1024  # 15 MB

@router.post("/api/proposal/extract")
async def api_extract_proposal(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Extracts text, sections, requirements, and structured metadata from an uploaded proposal PDF/DOCX."""
    filename = file.filename or "uploaded_proposal.pdf"
    ext = os.path.splitext(filename.lower())[1]

    if ext not in ALLOWED_PROPOSAL_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only PDF, DOCX, and TXT files are supported."
        )

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        if len(file_bytes) > MAX_PROPOSAL_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of 15 MB ({len(file_bytes) / (1024*1024):.1f} MB uploaded)."
            )

        # Validate and build proposal profile first
        profile = build_proposal_profile(file_bytes, filename)

        # Save validated file to uploads/proposals for browser viewing
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "proposals")
        os.makedirs(uploads_dir, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        save_path = os.path.join(uploads_dir, safe_name)
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        profile["file_url"] = f"/uploads/proposals/{safe_name}"
        return profile
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Proposal extraction error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to extract proposal requirements from file.")


@router.get("/api/proposal/parameters")
def api_get_proposal_parameters():
    """Returns the complete catalog of 15 proposal analysis parameters."""
    params = get_parameter_catalog()
    return {
        "parameters": params,
        "count": len(params)
    }


@router.post("/api/proposal/recommend-parameters")
def api_recommend_parameters(payload: RecommendParametersRequest):
    """
    Evaluates all 15 parameters against the extracted Proposal Profile using Gemini or Ollama.
    Returns recommended parameter IDs and comprehensive per-parameter evaluations with reasons and RFP evidence.
    """
    try:
        evaluations = evaluate_all_parameters(payload.proposal_profile)
        recommended = [p["parameter_id"] for p in evaluations if p.get("recommendation") == "recommended"]
        return {
            "recommended_parameters": recommended,
            "parameter_evaluations": evaluations,
            "count": len(recommended)
        }
    except RuntimeError as re:
        logger.error("[ProposalRoutes] AI parameter recommendation failed: %s", re)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )


@router.post("/api/proposal/analyze")
def api_analyze_proposal(
    payload: ProposalAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes Proposal-Based Prospect Analysis.
    Evaluates how well the selected prospect fits the uploaded proposal across user-selected parameters.
    """
    if not payload.prospect_name or not payload.prospect_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please select a prospect before starting analysis.")

    if not payload.selected_parameters:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please select at least one analysis parameter.")

    try:
        result = analyze_proposal_fit(
            db=db,
            current_user=current_user,
            prospect_id=payload.prospect_id,
            prospect_name=payload.prospect_name.strip(),
            proposal_profile=payload.proposal_profile,
            selected_parameters=payload.selected_parameters,
            mock_mode=payload.mock_mode or False
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        logger.error("[ProposalRoutes] AI Proposal analysis unavailable for %s: %s", payload.prospect_name, re)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "ai_services_unavailable",
                "valid": False,
                "message": str(re),
                "reason": str(re),
                "prospect_name": payload.prospect_name
            }
        )
    except Exception as e:
        logger.error("Proposal analysis error for %s: %s", payload.prospect_name, e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Proposal analysis failed: {str(e)}")


@router.post("/api/proposal/analyze/stream")
def api_analyze_proposal_stream(
    payload: ProposalAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes Proposal-Based Prospect Analysis concurrently and streams progressive results via SSE.
    """
    if not payload.prospect_name or not payload.prospect_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please select a prospect before starting analysis.")

    if not payload.selected_parameters:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please select at least one analysis parameter.")

    try:
        valid_ids = validate_selected_parameters(payload.selected_parameters)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    def event_generator():
        try:
            for sse_chunk in stream_proposal_analysis(
                db=db,
                current_user=current_user,
                prospect_id=payload.prospect_id,
                prospect_name=payload.prospect_name.strip(),
                proposal_profile=payload.proposal_profile,
                selected_parameters=valid_ids,
                mock_mode=payload.mock_mode or False
            ):
                yield sse_chunk
        except Exception as e:
            logger.error("[ProposalRoutes] Streaming error for %s: %s", payload.prospect_name, e, exc_info=True)
            yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

