from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any

from models import User, ProspectAnalysisDB
from models.validation_contract import ValidatedProspectAnalysisInput
from services.output_guardrails import validate_analysis_output
from research.orchestrator import research_prospect
from analysis.summarizer import summarize_all_parameters
from helpers import (
    verify_prospect_evidence,
    normalize_analysis_payload,
)

logger = logging.getLogger(__name__)

def calculate_overall_prospect_score(report_data: dict) -> dict:
    """Legacy helper maintained for signature compatibility - numerical scoring disabled."""
    return {"overall_score": None, "confidence": "High", "warning_message": None}



def run_prospect_analysis(
    db: Session,
    current_user: User,
    validated_input: ValidatedProspectAnalysisInput,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    EMPIRICAL PROSPECT ANALYSIS ENGINE (GENERAL PROSPECT INTELLIGENCE).
    MANDATORY GATE: Requires a ValidatedProspectAnalysisInput instance.
    """
    # 1. HARD ARCHITECTURAL GATE ENFORCEMENT
    if not isinstance(validated_input, ValidatedProspectAnalysisInput):
        logger.critical(
            "[CRITICAL SAFETY GATE VIOLATION] Unvalidated input passed directly to analysis engine: %s - %s",
            type(validated_input),
            validated_input
        )
        raise TypeError(
            "run_prospect_analysis requires a ValidatedProspectAnalysisInput instance."
        )

    prospect_name = validated_input.prospect
    domain_name = validated_input.domain or "Insurance"
    extra_params = validated_input.parameters or []

    logger.info("Analysis requested for '%s' (Domain: %s | Mode: GENERAL)", prospect_name, domain_name)

    # Fast-path for mock_mode (unit testing & automated test suites)
    if getattr(validated_input, 'mock_mode', False):
        mock_report_data = {
            "Company Scale": {"summary": f"Assets and scale for {prospect_name}.", "key_facts": [f"Scale observation for {prospect_name}"]},
            "Financial Strength": {"summary": f"High solvency ratio of 1.95x and AAA rating for {prospect_name}.", "key_facts": ["Solvency ratio 1.95x", "AAA rated balance sheet"]},
            "Insurance Performance": {"summary": f"Combined ratio 93.5% and strong underwriting profit for {prospect_name}.", "key_facts": ["Combined ratio 93.5%"]},
            "Business Growth": {"summary": f"Premium expanded by 14.8% YoY for {prospect_name}.", "key_facts": ["14.8% YoY growth"]},
            "Market Position": {"summary": f"Ranked top tier insurance provider for {prospect_name}.", "key_facts": ["Top tier market share"]},
            "Operational Scale": {"summary": f"Extensive multi-channel distribution network for {prospect_name}.", "key_facts": ["Multi-channel distribution"]},
            "Technology Activity": {"summary": f"AI underwriting platform and cloud infrastructure for {prospect_name}.", "key_facts": ["AI underwriting platform"]},
            "Strategic Activity": {"summary": f"Strategic bancassurance partnerships for {prospect_name}.", "key_facts": ["Key bancassurance alliances"]}
        }

        db_entry = ProspectAnalysisDB(
            user_uuid=current_user.uuid,
            user_id=current_user.id,
            company_name=prospect_name,
            analysis_mode="GENERAL",
            proposal_details=None,
            proposal_filename=None,
            risk_rating="N/A",
            report_data=mock_report_data,
            executive_summary=f"Executive underwriting synthesis for {prospect_name}.",
            score=None,
            avg_confidence_level="High",
            chat_history=[],
            pipeline_version="2.1.0"
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)

        mock_output = {
            "id": db_entry.id,
            "user_uuid": db_entry.user_uuid,
            "user_id": db_entry.user_id,
            "company_name": db_entry.company_name,
            "analysis_mode": db_entry.analysis_mode,
            "proposal_details": db_entry.proposal_details,
            "proposal_filename": db_entry.proposal_filename,
            "risk_rating": db_entry.risk_rating,
            "executive_summary": db_entry.executive_summary,
            "overall_score": db_entry.score,
            "overall_confidence": db_entry.avg_confidence_level,
            "report_data": db_entry.report_data,
            "metrics_scorecard": {
                "solvency_ratio": {"value": "1.95x", "status": "Strong", "period": "FY24", "source": "Statutory Annual Filing"},
                "combined_ratio": {"value": "93.5%", "status": "Underwriting Profit (<100%)", "period": "FY24", "source": "Audited Public Disclosures"},
                "gross_written_premium": {"value": "14.8% YoY", "growth_yoy": "+14.8%"},
                "credit_rating": {"agency": "CRISIL / AM Best", "grade": "AAA / A+", "outlook": "Stable"}
            },
            "chat_history": [],
            "messages": [],
            "created_at": db_entry.created_at.isoformat() if db_entry.created_at else None,
            "is_cached": False,
            "is_historical": False,
            "pipeline_version": "2.1.0"
        }
        return validate_analysis_output(mock_output)

    # 3. Live Empirical Research & Analysis Pipeline
    try:
        logger.info("[ANALYSIS ENGINE] Searching public research sources for '%s'...", prospect_name)
        evidence_by_param = research_prospect(
            prospect_name=prospect_name,
            extra_parameters=extra_params
        )

        prospect_validated, validation_reason = verify_prospect_evidence(prospect_name, evidence_by_param)

        if not prospect_validated:
            logger.warning("[ANALYSIS ENGINE] Insufficient public disclosures found for '%s' (%s).", prospect_name, validation_reason)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "analysis_failed",
                    "valid": False,
                    "error": "DATA_NOT_FOUND",
                    "message": "I couldn't complete the analysis for this prospect right now. Please try the analysis again.",
                    "prospect_name": prospect_name
                }
            )

        logger.info("[ANALYSIS ENGINE] Synthesizing research metrics for '%s' (Mode: GENERAL)...", prospect_name)
        
        analysis_result = summarize_all_parameters(prospect_name, evidence_by_param)
        overall_score = None
        verdict = analysis_result.get("underwriting_verdict") or {}
        risk_rating = verdict.get("overall_risk_level") or analysis_result.get("risk_rating") or "Medium"
        underwriting_verdict = {
            "overall_risk_level": risk_rating,
            "primary_exposure_classes": verdict.get("primary_exposure_classes") or ["Property / BI", "General Liability", "Workers Compensation"],
            "entry_point_trigger": verdict.get("entry_point_trigger") or "No immediate entry point identified"
        }
        critical_data_gaps = analysis_result.get("critical_data_gaps") or []

        report_dict = analysis_result.get("parameters", {})
        exec_summary = analysis_result.get("executive_summary", "")
        overall_confidence = analysis_result.get("overall_confidence", "High")
        normalized_report = normalize_analysis_payload(report_dict)

        db_entry = ProspectAnalysisDB(
            user_uuid=current_user.uuid,
            user_id=current_user.id,
            company_name=prospect_name,
            analysis_mode="GENERAL",
            proposal_details=None,
            proposal_filename=None,
            risk_rating=risk_rating,
            critical_data_gaps=critical_data_gaps,
            report_data=normalized_report,
            executive_summary=exec_summary,
            score=None,
            avg_confidence_level=overall_confidence,
            chat_history=[],
            pipeline_version="2.1.0"
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)

        logger.info("Analysis completed for '%s' in GENERAL mode", prospect_name)

        raw_output = {
            "id": db_entry.id,
            "user_uuid": db_entry.user_uuid,
            "user_id": db_entry.user_id,
            "company_name": db_entry.company_name,
            "analysis_mode": db_entry.analysis_mode,
            "proposal_details": db_entry.proposal_details,
            "proposal_filename": db_entry.proposal_filename,
            "risk_rating": db_entry.risk_rating,
            "executive_summary": db_entry.executive_summary,
            "overall_score": db_entry.score,
            "overall_confidence": db_entry.avg_confidence_level,
            "report_data": db_entry.report_data,
            "underwriting_verdict": underwriting_verdict,
            "critical_data_gaps": critical_data_gaps,
            "metrics_scorecard": analysis_result.get("metrics_scorecard", {}),
            "chat_history": db_entry.chat_history or [],
            "messages": db_entry.chat_history or [],
            "created_at": db_entry.created_at.isoformat() if db_entry.created_at else None,
            "is_cached": False,
            "is_historical": False,
            "pipeline_version": "2.1.0"
        }

        # 4. Output Guardrail Validation
        return validate_analysis_output(raw_output)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error in run_prospect_analysis for %s: %s", prospect_name, e, exc_info=True)
        err_str = str(e)
        if any(k in err_str.lower() for k in ["summarization failed", "ai summarization service", "ai proposal analysis", "quota", "ollama", "gemini"]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "ai_services_unavailable",
                    "valid": False,
                    "message": f"AI analysis service is temporarily unavailable for {prospect_name}.",
                    "reason": err_str,
                    "prospect_name": prospect_name
                }
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "analysis_failed",
                "valid": False,
                "message": "I couldn't complete the analysis for this prospect right now. Please try the analysis again.",
                "reason": str(e),
                "prospect_name": prospect_name
            }
        )

def get_user_analyses(db: Session, current_user: User) -> list:
    """Returns analyses belonging to the currently authenticated user by UUID."""
    analyses = db.query(ProspectAnalysisDB).filter(
        (ProspectAnalysisDB.user_uuid == current_user.uuid) | (ProspectAnalysisDB.user_id == current_user.id)
    ).order_by(ProspectAnalysisDB.created_at.desc()).all()

    return [
        {
            "id": item.id,
            "user_uuid": item.user_uuid or current_user.uuid,
            "user_id": item.user_id,
            "company_name": item.company_name,
            "analysis_mode": item.analysis_mode or "GENERAL",
            "proposal_filename": item.proposal_filename,
            "risk_rating": item.risk_rating or "N/A",
            "executive_summary": item.executive_summary,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "parameter_count": len(item.report_data) if item.report_data else 0,
            "pipeline_version": getattr(item, "pipeline_version", None) or "2.1.0"
        }
        for item in analyses
    ]

def get_user_analysis_by_id(db: Session, current_user: User, analysis_id: int) -> dict:
    """Retrieves a single analysis by ID."""
    item = db.query(ProspectAnalysisDB).filter(
        ProspectAnalysisDB.id == analysis_id,
        (ProspectAnalysisDB.user_uuid == current_user.uuid) | (ProspectAnalysisDB.user_id == current_user.id)
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis report not found or access denied."
        )

    overall_info = calculate_overall_prospect_score(item.report_data or {})

    overall_risk = item.risk_rating or "Medium"
    if overall_risk == "N/A":
        overall_risk = "Medium"

    underwriting_verdict = {
        "overall_risk_level": overall_risk,
        "primary_exposure_classes": ["Property / BI", "General Liability", "Workers Compensation", "Cyber"],
        "entry_point_trigger": "Identified from commercial underwriting intelligence analysis." if item.analysis_mode != "PROPOSAL" else f"Proposal Document Analysis ({item.proposal_filename or 'Direct'})"
    }

    return {
        "id": item.id,
        "user_uuid": item.user_uuid or current_user.uuid,
        "user_id": item.user_id,
        "company_name": item.company_name,
        "analysis_mode": item.analysis_mode or "GENERAL",
        "proposal_details": item.proposal_details,
        "proposal_filename": item.proposal_filename,
        "risk_rating": item.risk_rating or "N/A",
        "executive_summary": item.executive_summary,
        "overall_score": item.score if item.score is not None else overall_info.get("overall_score"),
        "overall_confidence": item.avg_confidence_level or overall_info.get("confidence"),
        "score_warning": overall_info.get("warning_message"),
        "report_data": item.report_data,
        "underwriting_verdict": underwriting_verdict,
        "critical_data_gaps": item.critical_data_gaps or [],
        "chat_history": item.chat_history or [],
        "messages": item.chat_history or [],
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "is_cached": True,
        "is_historical": True,
        "pipeline_version": getattr(item, "pipeline_version", None) or "2.1.0"
    }

def delete_user_analysis_by_id(db: Session, current_user: User, analysis_id: int) -> dict:
    """Deletes an analysis record belonging to the authenticated user."""
    item = db.query(ProspectAnalysisDB).filter(
        ProspectAnalysisDB.id == analysis_id,
        (ProspectAnalysisDB.user_uuid == current_user.uuid) | (ProspectAnalysisDB.user_id == current_user.id)
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis report not found or access denied."
        )

    db.delete(item)
    db.commit()
    return {"message": f"Analysis {analysis_id} deleted successfully."}
