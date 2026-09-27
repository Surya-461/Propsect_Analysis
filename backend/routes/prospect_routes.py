import logging
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from schemas.prospect import ProspectValidationRequest
from schemas.validation import ValidationStatusEnum
from services.validation_gateway import ProspectValidationGateway
from services.prospect_service import search_prospects
from ai.gemini import GEMINI_MODEL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Prospect Registry & Metadata"])

@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "auth": "JWT Protected (UUID Auth)",
            "ai_provider": f"Google Gemini ({GEMINI_MODEL}) (Primary) + Local Ollama Fallback"
        }
    except Exception as e:
        logger.error("Health check failed on database ping: %s", e)
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": f"error: {str(e)}",
                "auth": "JWT Protected (UUID Auth)",
                "ai_provider": f"Google Gemini ({GEMINI_MODEL}) (Primary) + Local Ollama Fallback"
            }
        )

@router.get("/prospects/search")
def search_prospect_directory(q: Optional[str] = None, limit: int = 15):
    results = search_prospects(q or "", limit=limit)
    return {"results": results, "count": len(results)}

@router.post("/prospects/resolve")
def validate_prospect(req: ProspectValidationRequest):
    raw_input = (req.prospect_name or "").strip()
    domain_name = req.domain or "Insurance"

    val_res = ProspectValidationGateway.validate_prospect_input(
        user_input=raw_input,
        custom_context={"domain": domain_name}
    )

    if not val_res.valid:
        return {
            "status": "not_found" if val_res.status == ValidationStatusEnum.INVALID else "needs_clarification",
            "valid": False,
            "prospect_name": raw_input,
            "domain": domain_name,
            "message": val_res.reason or "I couldn't find that company in the currently supported insurance prospects. Please select a company from the available prospect list.",
            "candidates": val_res.candidates,
            "clarification": val_res.clarification.dict() if val_res.clarification else None
        }

    return {
        "status": "valid",
        "valid": True,
        "prospect_name": val_res.prospect or raw_input,
        "prospect_id": val_res.prospect_id,
        "domain": domain_name,
        "confidence": 1.0,
        "reason": f"✓ Prospect verified: {val_res.prospect}"
    }
