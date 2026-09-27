import json
import uuid
import datetime
import logging
from typing import Optional, Dict, Any

from models.validation_contract import (
    ValidationStatusEnum,
    ValidatedProspectAnalysisInput,
    ValidationErrorItem,
    ClarificationOption,
    ValidationResultContract,
)
from services.prospect_service import resolve_prospect
from config.domain_schemas import get_domain_schema

logger = logging.getLogger(__name__)


class ProspectValidationGateway:
    """
    JSON-BACKED PROSPECT RESOLUTION GATEWAY.
    Resolves prospect names against the authoritative backend/data/insurance_prospects_250.json repository.
    Deterministic, fast, and maintains 100% fidelity without LLM entity hallucinations.
    """

    @classmethod
    def validate_prospect_input(
        cls,
        user_input: str,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> ValidationResultContract:
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        context = custom_context or {}
        raw_text = (user_input or "").strip()
        domain_name = context.get("domain") or "Insurance"
        if not domain_name or domain_name.lower() in ["prospect_analysis", "default", ""]:
            domain_name = "Insurance"

        def log_audit(status: ValidationStatusEnum, confidence: float, prospect: Optional[str], reason: Optional[str], analysis_started: bool):
            audit_entry = {
                "requestId": request_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "rawInput": raw_text,
                "validationStatus": status.value,
                "prospect": prospect,
                "domain": domain_name,
                "confidence": confidence,
                "reason": reason,
                "analysisStarted": analysis_started
            }
            logger.info("[PROSPECT RESOLUTION AUDIT] %s", json.dumps(audit_entry))

        # STAGE 1: Basic Input Sanity Guardrails (Domain, Empty, Length)
        # ----------------------------------------------------------------------
        try:
            domain_schema = get_domain_schema(domain_name)
        except KeyError as err:
            err_msg = str(err).strip("'\"")
            log_audit(ValidationStatusEnum.INVALID, 0.0, None, err_msg, False)
            return ValidationResultContract(
                valid=False,
                status=ValidationStatusEnum.INVALID,
                domain=domain_name,
                confidence=0.0,
                reason=err_msg,
                errors=[ValidationErrorItem(code="DOMAIN_UNSUPPORTED", message=err_msg)]
            )

        if not raw_text or not isinstance(raw_text, str):
            err = ValidationErrorItem(code="PROSPECT_REQUIRED", message="Please enter a prospect name for analysis.")
            log_audit(ValidationStatusEnum.INVALID, 0.0, None, "Empty input.", False)
            return ValidationResultContract(
                valid=False,
                status=ValidationStatusEnum.INVALID,
                domain=domain_name,
                confidence=0.0,
                reason="Please enter a prospect name for analysis.",
                errors=[err]
            )

        if len(raw_text) < 2:
            err = ValidationErrorItem(code="INPUT_TOO_SHORT", message="Please enter a valid prospect name for analysis.")
            log_audit(ValidationStatusEnum.INVALID, 0.1, None, "Input too short.", False)
            return ValidationResultContract(
                valid=False,
                status=ValidationStatusEnum.INVALID,
                domain=domain_name,
                confidence=0.1,
                reason="Input is too short. Minimum 2 characters required.",
                errors=[err]
            )

        if len(raw_text) > 250:
            err = ValidationErrorItem(code="INPUT_TOO_LONG", message="Input exceeds maximum allowed length.")
            log_audit(ValidationStatusEnum.INVALID, 0.1, None, "Input too long.", False)
            return ValidationResultContract(
                valid=False,
                status=ValidationStatusEnum.INVALID,
                domain=domain_name,
                confidence=0.1,
                reason="Input exceeds maximum allowed length of 250 characters.",
                errors=[err]
            )

        # ----------------------------------------------------------------------
        # STAGE 2: Deterministic JSON Universe Prospect Resolution
        # ----------------------------------------------------------------------
        matched_record, candidates, resolution_status = resolve_prospect(raw_text)

        # CASE A: Ambiguous match with multiple candidates (e.g. user typed "SBI")
        if resolution_status == "MULTIPLE_MATCHES" and candidates:
            candidate_names = [c["name"] for c in candidates]
            clarification = ClarificationOption(
                question="Multiple matching prospects found. Please select one:",
                options=candidate_names
            )
            reason_msg = "Multiple matching prospects found in the supported insurance directory. Please select the specific company."
            log_audit(ValidationStatusEnum.NEEDS_CLARIFICATION, 0.5, None, reason_msg, False)
            return ValidationResultContract(
                valid=False,
                status=ValidationStatusEnum.NEEDS_CLARIFICATION,
                domain=domain_name,
                confidence=0.5,
                reason=reason_msg,
                candidates=candidates,
                clarification=clarification
            )

        # CASE B: Prospect Not Found in JSON Universe
        if not matched_record:
            friendly_msg = "I couldn't find that company in the currently supported insurance prospects. Please select a company from the available prospect list."
            err = ValidationErrorItem(code="PROSPECT_NOT_FOUND", message=friendly_msg)
            log_audit(ValidationStatusEnum.INVALID, 0.0, raw_text, "Prospect not found in JSON universe.", False)
            return ValidationResultContract(
                valid=False,
                status=ValidationStatusEnum.INVALID,
                prospect=raw_text,
                domain=domain_name,
                confidence=0.0,
                reason=friendly_msg,
                candidates=candidates,
                errors=[err]
            )

        # ----------------------------------------------------------------------
        # STAGE 3: Canonical Match Found - Build Validated Analysis Input
        # ----------------------------------------------------------------------
        canonical_name = matched_record["name"]
        canonical_id = matched_record.get("id")

        canonical_params = domain_schema.get("default_parameters", [
            "Company Scale",
            "Business Growth",
            "Market Position",
            "Financial Strength",
            "Insurance Performance",
            "Operational Scale",
            "Technology Activity",
            "Strategic Activity"
        ])

        extra_params = context.get("extra_parameters")
        normalized_params = extra_params if (extra_params and isinstance(extra_params, list) and len(extra_params) > 0) else list(canonical_params)

        normalized_input = ValidatedProspectAnalysisInput(
            prospect=canonical_name,
            prospect_id=canonical_id,
            domain=domain_name,
            intent="prospect_analysis",
            parameters=normalized_params,
            geography=context.get("geography", "Global"),
            period=context.get("period", "FY2024-25"),
            confidence=1.0,
            mock_mode=context.get("mock_mode", False)
        )

        log_audit(ValidationStatusEnum.VALID, 1.0, canonical_name, f"Resolved via {resolution_status}", True)

        return ValidationResultContract(
            valid=True,
            status=ValidationStatusEnum.VALID,
            prospect=canonical_name,
            prospect_id=canonical_id,
            domain=domain_name,
            intent="prospect_analysis",
            parameters=normalized_params,
            confidence=1.0,
            reason=f"Canonical prospect '{canonical_name}' verified from insurance directory.",
            candidates=[matched_record],
            normalizedInput=normalized_input
        )
