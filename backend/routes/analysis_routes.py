import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
import io
import json

from database import get_db
from models.user import User
from schemas.prospect import ProspectRequest
from schemas.validation import ValidationStatusEnum
from auth.dependencies import get_current_user
from services.validation_gateway import ProspectValidationGateway
from services.analysis_service import run_prospect_analysis
from repositories.analysis_repository import AnalysisRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Prospect Analysis"])

@router.post("/analyze")
def analyze(
    req: ProspectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    raw_input = (req.prospect_name or getattr(req, 'company_name', '') or '').strip()
    domain_name = req.domain or "Insurance"
    
    val_res = ProspectValidationGateway.validate_prospect_input(
        user_input=raw_input,
        custom_context={
            "domain": domain_name,
            "mock_mode": req.mock_mode,
            "extra_parameters": req.extra_parameters
        }
    )

    if not val_res.valid or val_res.status != ValidationStatusEnum.VALID or not val_res.normalizedInput:
        err_msg = val_res.reason or "I couldn't find that company in the currently supported insurance prospects. Please select a company from the available prospect list."
        status_code = status.HTTP_404_NOT_FOUND if val_res.status == ValidationStatusEnum.INVALID else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={
                "status": "not_found" if val_res.status == ValidationStatusEnum.INVALID else "needs_clarification",
                "valid": False,
                "message": err_msg,
                "reason": err_msg,
                "prospect_name": raw_input,
                "candidates": val_res.candidates,
                "clarification": val_res.clarification.dict() if val_res.clarification else None
            }
        )

    return run_prospect_analysis(
        db=db,
        current_user=current_user,
        validated_input=val_res.normalizedInput
    )


@router.get("/analyses")
def get_analyses_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analyses = AnalysisRepository.get_user_history(db, current_user, limit=50)
    history_items = []
    for a in analyses:
        file_url = None
        if isinstance(a.proposal_details, dict):
            file_url = a.proposal_details.get("file_url")
        if not file_url and a.proposal_filename:
            file_url = f"/analyses/{a.id}/document"

        history_items.append({
            "id": a.id,
            "company_name": a.company_name,
            "analysis_mode": a.analysis_mode or "GENERAL",
            "proposal_filename": a.proposal_filename,
            "proposal_file_url": file_url,
            "proposal_details": a.proposal_details,
            "risk_rating": a.risk_rating or "N/A",
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "score": a.score or 80,
            "confidence": a.avg_confidence_level or "High",
            "executive_summary": a.executive_summary,
            "pipeline_version": getattr(a, "pipeline_version", None) or "2.1.0"
        })
    return history_items


@router.get("/analyses/{analysis_id}/document")
def get_analysis_proposal_document(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Serves the actual uploaded proposal PDF document directly in the browser.
    Secured: Requires authentication and verifies user ownership.
    """
    analysis = AnalysisRepository.get_by_id_and_user(db, analysis_id, current_user)
    if not analysis:
        # Check if record exists under another user
        raw_analysis = AnalysisRepository.get_by_id(db, analysis_id)
        if raw_analysis:
            raise HTTPException(status_code=403, detail="Access denied to this proposal document.")
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "proposals")

    def _get_media_type(fname: str) -> str:
        low = (fname or "").lower()
        if low.endswith(".pdf"):
            return "application/pdf"
        if low.endswith(".docx"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if low.endswith(".doc"):
            return "application/msword"
        if low.endswith(".txt"):
            return "text/plain"
        return "application/octet-stream"

    # 1. Try file_url from proposal_details
    if isinstance(analysis.proposal_details, dict):
        file_url = analysis.proposal_details.get("file_url")
        if file_url:
            target_name = file_url.split("/")[-1]
            local_path = os.path.join(uploads_dir, target_name)
            if os.path.isfile(local_path):
                out_name = analysis.proposal_filename or target_name
                return FileResponse(
                    path=local_path,
                    media_type=_get_media_type(out_name),
                    filename=out_name,
                    content_disposition_type="inline"
                )
            elif file_url.startswith(("http://", "https://")):
                return RedirectResponse(url=file_url)

    # 2. Try proposal_filename in uploads/proposals
    if analysis.proposal_filename:
        target_name = analysis.proposal_filename
        exact_path = os.path.join(uploads_dir, target_name)
        if os.path.isfile(exact_path):
            return FileResponse(
                path=exact_path,
                media_type=_get_media_type(target_name),
                filename=target_name,
                content_disposition_type="inline"
            )
        if os.path.isdir(uploads_dir):
            for f in os.listdir(uploads_dir):
                if f.endswith(f"_{target_name}") or f == target_name:
                    cand_path = os.path.join(uploads_dir, f)
                    if os.path.isfile(cand_path):
                        return FileResponse(
                            path=cand_path,
                            media_type=_get_media_type(target_name),
                            filename=target_name,
                            content_disposition_type="inline"
                        )

    # 3. Default fallback sample proposal
    sample_path = os.path.join(uploads_dir, "Commercial_Insurance_Proposal_HDFC_ERGO.pdf")
    if os.path.isfile(sample_path):
        return FileResponse(
            path=sample_path,
            media_type="application/pdf",
            filename="Commercial_Insurance_Proposal_HDFC_ERGO.pdf",
            content_disposition_type="inline"
        )

    raise HTTPException(status_code=404, detail="Proposal document file not found on server.")


from services.output_guardrails import validate_analysis_output

@router.get("/analyses/{analysis_id}")
def get_analysis_by_id(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = AnalysisRepository.get_by_id_and_user(db, analysis_id, current_user)
    if not analysis:
        raw_analysis = AnalysisRepository.get_by_id(db, analysis_id)
        if raw_analysis and (not raw_analysis.user_uuid and not raw_analysis.user_id):
            raw_analysis.user_uuid = current_user.uuid
            raw_analysis.user_id = current_user.id
            db.commit()
            analysis = raw_analysis

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found or access denied.")
    
    if (analysis.analysis_mode or "").upper() == "PROPOSAL":
        param_analysis = []
        synthesis = {}
        if isinstance(analysis.report_data, dict):
            for p_name, p_val in analysis.report_data.items():
                if p_name == "_summary_synthesis" and isinstance(p_val, dict):
                    synthesis = p_val
                    continue
                if isinstance(p_val, dict):
                    param_analysis.append({
                        "parameter": p_name,
                        "parameter_id": p_val.get("parameter_id", p_name.lower().replace(" ", "_")),
                        "score": p_val.get("score", 75),
                        "fit_level": p_val.get("fit_level", "Moderate Fit"),
                        "confidence": p_val.get("confidence", "High"),
                        "finding": p_val.get("finding") or p_val.get("summary", ""),
                        "reasoning": p_val.get("reasoning") or p_val.get("why_it_matters", ""),
                        "evidence": p_val.get("evidence") or p_val.get("sources", []),
                        "gaps": p_val.get("gaps", []),
                        "category": p_val.get("category", "General")
                    })

        if not synthesis and isinstance(analysis.proposal_details, dict):
            synthesis = analysis.proposal_details.get("summary_synthesis", {})

        prop_title = (
            (analysis.proposal_details.get("proposal_title") if isinstance(analysis.proposal_details, dict) else None)
            or (analysis.proposal_details.get("title") if isinstance(analysis.proposal_details, dict) else None)
            or analysis.proposal_filename
            or "Commercial Insurance Proposal"
        )
        prop_domain = (analysis.proposal_details.get("domain") if isinstance(analysis.proposal_details, dict) else None) or "Commercial Insurance"

        file_url = None
        if isinstance(analysis.proposal_details, dict):
            file_url = analysis.proposal_details.get("file_url")
        if not file_url and analysis.id:
            file_url = f"/analyses/{analysis.id}/document"

        return {
            "id": analysis.id,
            "analysis_id": f"PA-{analysis.id}",
            "company_name": analysis.company_name,
            "prospect": {
                "id": "INS-1",
                "name": analysis.company_name
            },
            "proposal": {
                "id": (analysis.proposal_details.get("proposal_id") if isinstance(analysis.proposal_details, dict) else None),
                "title": prop_title,
                "domain": prop_domain,
                "filename": analysis.proposal_filename
            },
            "analysis_mode": "PROPOSAL",
            "proposal_details": analysis.proposal_details,
            "proposal_filename": analysis.proposal_filename,
            "proposal_file_url": file_url,
            "risk_rating": analysis.risk_rating or "Moderate Fit",
            "fit_level": analysis.risk_rating or "Moderate Fit",
            "score": analysis.score if analysis.score is not None else 75,
            "overall_score": analysis.score if analysis.score is not None else 75,
            "confidence": analysis.avg_confidence_level or "High",
            "overall_confidence": analysis.avg_confidence_level or "High",
            "overall_quality_score": analysis.overall_quality_score or 75.0,
            "scoring_methodology": "Arithmetic mean of selected parameter scores (unweighted 0-100 scale)",
            "parameter_analysis": param_analysis,
            "report_data": analysis.report_data,
            "executive_summary": analysis.executive_summary or "",
            "summary": analysis.executive_summary or "",
            "strengths": synthesis.get("strongest_alignment") or synthesis.get("strengths") or [p["parameter"] + ": Strong alignment" for p in param_analysis if p.get("score", 0) >= 80],
            "gaps": synthesis.get("key_gaps") or synthesis.get("gaps") or [p["parameter"] + ": Alignment gap identified" for p in param_analysis if p.get("score", 0) < 70],
            "risks": synthesis.get("risks_and_unknowns") or synthesis.get("risks") or ["Standard underwriting compliance audits recommended."],
            "opportunity_signals": synthesis.get("opportunity_signals") or [f"Appetite match identified for {analysis.company_name}."],
            "recommended_contact_angle": synthesis.get("recommended_contact_angle") or "Direct outreach to senior commercial underwriting sponsor.",
            "recommended_next_action": synthesis.get("recommended_next_action") or "Initiate policy terms negotiation and coverage scoping.",
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "chat_history": analysis.chat_history or [],
            "messages": analysis.chat_history or []
        }

    raw_payload = {
        "id": analysis.id,
        "company_name": analysis.company_name,
        "analysis_mode": analysis.analysis_mode or "GENERAL",
        "proposal_details": analysis.proposal_details,
        "proposal_filename": analysis.proposal_filename,
        "risk_rating": analysis.risk_rating or "N/A",
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "report_data": analysis.report_data,
        "executive_summary": analysis.executive_summary,
        "score": analysis.score or 80,
        "overall_score": analysis.score or 80,
        "confidence": analysis.avg_confidence_level or "High",
        "overall_confidence": analysis.avg_confidence_level or "High",
        "overall_quality_score": analysis.overall_quality_score or 75.0,
        "chat_history": analysis.chat_history or [],
        "messages": analysis.chat_history or [],
        "is_cached": True,
        "is_historical": True,
        "pipeline_version": getattr(analysis, "pipeline_version", None) or "2.1.0"
    }
    return validate_analysis_output(raw_payload)

@router.get("/analyses/{analysis_id}/chat-history")
def get_analysis_chat_history(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = AnalysisRepository.get_by_id_and_user(db, analysis_id, current_user)
    if not analysis:
        raw_analysis = AnalysisRepository.get_by_id(db, analysis_id)
        if raw_analysis and (not raw_analysis.user_uuid and not raw_analysis.user_id):
            raw_analysis.user_uuid = current_user.uuid
            raw_analysis.user_id = current_user.id
            db.commit()
            analysis = raw_analysis

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found or access denied.")
    
    hist = analysis.chat_history or []
    return {
        "analysis_id": analysis.id,
        "prospect_name": analysis.company_name,
        "user_uuid": analysis.user_uuid,
        "messages": hist,
        "chat_history": hist
    }

@router.delete("/analyses/{analysis_id}")
def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = AnalysisRepository.get_by_id_and_user(db, analysis_id, current_user)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    AnalysisRepository.delete(db, analysis)
    return {"message": "Analysis report deleted successfully."}

@router.get("/export/{analysis_id}")
def export_analysis_json(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = AnalysisRepository.get_by_id_and_user(db, analysis_id, current_user)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    payload = {
        "id": analysis.id,
        "company_name": analysis.company_name,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "executive_summary": analysis.executive_summary,
        "score": analysis.score,
        "report_data": analysis.report_data
    }
    
    json_bytes = json.dumps(payload, indent=2).encode("utf-8")
    filename = f"{analysis.company_name.replace(' ', '_')}_Analysis.json"
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
