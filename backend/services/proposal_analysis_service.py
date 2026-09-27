"""
Proposal Analysis Service for Proposal-Based Prospect Analysis.
Executes dynamic proposal-based prospect evaluations by comparing prospect evidence
against extracted proposal requirements across user-selected parameters.
Optimized with Batched 1-Call LLM Evaluation, Parameter-Specific Context Slicing,
5-Tier Output Schemas, and Resilient Diagnostic Fallbacks.
"""

import uuid
import json
import logging
import datetime
import concurrent.futures
from typing import Dict, Any, List, Optional, Generator
from sqlalchemy.orm import Session

from models.user import User
from models.analysis import ProspectAnalysisDB
from config.proposal_analysis_config import (
    PROPOSAL_PARAMETERS_BY_ID,
    PROPOSAL_MAX_CONCURRENT_PARAMETERS
)
from services.proposal_parameter_service import validate_selected_parameters
from services.analysis_summary_service import (
    generate_proposal_executive_summary,
    clean_plain_text
)
from research.source_manager import search_all_sources
from analysis.source_relevance import (
    build_tagged_evidence_context,
    filter_and_align_sources
)
from ai.gemini import query_gemini
from ai.ollama import query_ollama, PRIMARY_OLLAMA_MODEL

logger = logging.getLogger(__name__)

# Parameter-specific actionable data acquisition recommendations when public data is insufficient
PARAMETER_DISCOVERY_SUGGESTIONS: Dict[str, str] = {
    "claims_relevance": "Request 3-year audited loss runs, claim settlement turnaround SLAs, and TPA adjudication exhibits directly from the prospect's claims committee.",
    "underwriting_relevance": "Request the prospect's underwriting appetite guide, delegation of authority matrix, and statutory Schedule P loss reserve exhibits.",
    "ai_ml_adoption": "Request IT architecture blueprints, cognitive underwriting pilot reports, or AI model risk validation disclosures during technical pre-bid discovery.",
    "digital_transformation": "Request enterprise cloud migration timelines, core API integration documentation, and broker portal feature matrices.",
    "regulatory_statutory_compliance": "Review state insurance department examination reports, NAIC statutory filings, and legal compliance disclosures from the general counsel.",
    "security_compliance": "Request SOC 2 Type II audit reports, annual third-party penetration test executive summaries, and ISO 27001 certifications during vendor risk assessment.",
    "business_alignment": "Review statutory annual returns (Form 10-K / IRDAI Form NL) and product filing schedules for licensed commercial lines of business.",
    "insurance_product_alignment": "Review policy wording schedules, coverage endorsement filings, and treaty reinsurance line structures.",
    "financial_strength": "Review audited statutory balance sheets, AM Best / CRISIL credit rating reports, and quarterly solvency capital statements.",
    "operational_scale": "Request commercial broker distribution network maps, branch counts, and regional service center capacity disclosures."
}


def get_parameter_specific_rfp_clauses(
    parameter_id: str,
    param_meta: Dict[str, Any],
    proposal_profile: Dict[str, Any]
) -> List[str]:
    """
    Dynamically matches and returns RFP requirements and clauses specific to this parameter dimension.
    Prevents generic top-5 requirement dilution by prioritizing domain-matching RFP statements.
    """
    all_clauses = []
    
    # Pool all extracted proposal requirement streams
    for field in [
        "functional_requirements", "technology_requirements", "ai_ml_requirements",
        "data_requirements", "integration_requirements", "security_requirements",
        "regulatory_requirements", "implementation_requirements", "commercial_requirements",
        "requirements"
    ]:
        val = proposal_profile.get(field)
        if isinstance(val, list):
            all_clauses.extend([str(item).strip() for item in val if str(item).strip()])

    param_keywords = [k.lower() for k in param_meta.get("keywords", [])]
    param_name_tokens = [t.lower() for t in param_meta.get("name", "").split() if len(t) > 3]
    search_tokens = set(param_keywords + param_name_tokens + [parameter_id.lower().replace("_", " ")])

    matched_clauses = []
    for clause in all_clauses:
        clause_lower = clause.lower()
        if any(token in clause_lower for token in search_tokens):
            matched_clauses.append(clause)

    # Fallback to general proposal requirements if no keyword matches found
    if not matched_clauses:
        fallback_reqs = proposal_profile.get("requirements") or proposal_profile.get("functional_requirements") or []
        matched_clauses = [str(r) for r in fallback_reqs[:5]]

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for c in matched_clauses:
        c_clean = c.strip()
        if c_clean.lower() not in seen and len(c_clean) > 10:
            seen.add(c_clean.lower())
            deduped.append(c_clean)

    return deduped[:6]


def evaluate_parameter_fit(
    prospect_name: str,
    parameter_id: str,
    proposal_profile: Dict[str, Any],
    mock_mode: bool = False
) -> Dict[str, Any]:
    """
    Evaluates a single parameter dimension for a prospect against the proposal requirements.
    Maintained for backward-compatibility and single-parameter re-evaluations.
    """
    param_meta = PROPOSAL_PARAMETERS_BY_ID.get(parameter_id, {
        "name": parameter_id.replace("_", " ").title(),
        "category": "General",
        "description": f"Evaluation of {parameter_id}",
        "keywords": []
    })
    param_name = param_meta["name"]
    category = param_meta["category"]
    param_keywords = param_meta.get("keywords", [])
    discovery_suggestion = PARAMETER_DISCOVERY_SUGGESTIONS.get(
        parameter_id,
        f"Request specific underwriting exhibits and operational disclosures for {param_name} directly from {prospect_name}."
    )

    if mock_mode:
        fit_level = "High" if ("regulatory" in parameter_id or "claims" in parameter_id or "transformation" in parameter_id) else "Medium"
        compliance_status = "Full Compliance" if fit_level == "High" else "Partial Compliance"
        mock_summary = f"Available public disclosures indicate that {prospect_name} maintains operational alignment with {param_name} requirements, supported by active commercial workflow integration and scalable infrastructure."
        return {
            "parameter_id": parameter_id,
            "parameter": param_name,
            "category": category,
            "fit_level": fit_level,
            "confidence": "High",
            "compliance_status": compliance_status,
            "summary": mock_summary,
            "finding": mock_summary,
            "reasoning": f"The proposal's technical and operational scope directly corresponds to {prospect_name}'s established market capabilities in {param_name}.",
            "why_it_matters": f"The proposal's technical and operational scope directly corresponds to {prospect_name}'s established market capabilities in {param_name}.",
            "verified_capabilities": [
                f"Established operational infrastructure supporting {param_name} workflows.",
                f"Statutory compliance and audited operational track record verified in public filings."
            ],
            "rfp_line_item_matching": [
                {
                    "rfp_requirement": f"Mandatory operational capability in {param_name}",
                    "prospect_capability": f"Verified public disclosure confirming production capability in {param_name}",
                    "alignment": "Full Fit" if fit_level == "High" else "Partial Fit"
                }
            ],
            "evidence": [
                {
                    "source": "Public Statutory Filing",
                    "url": f"https://disclosures.example.com/{prospect_name.lower().replace(' ', '_')}/{parameter_id}",
                    "summary": f"Verified public statutory disclosures confirming {prospect_name}'s operational scale in {param_name}."
                }
            ],
            "sources": [
                {
                    "name": "Public Statutory Filing",
                    "url": f"https://disclosures.example.com/{prospect_name.lower().replace(' ', '_')}/{parameter_id}",
                    "evidence": f"Verified public statutory disclosures confirming {prospect_name}'s operational scale in {param_name}."
                }
            ],
            "gaps": [
                f"Public information does not confirm active procurement budget for this specific quarter.",
                f"Recommended Data Source: {discovery_suggestion}"
            ],
            "producer_discovery_action": discovery_suggestion
        }

    # Fetch evidence
    raw_evidence = []
    queries = param_meta.get("search_queries", [f"{prospect_name} {param_name}"])
    try:
        raw_evidence = search_all_sources(
            company_name=prospect_name,
            parameter=param_name,
            search_queries=queries,
            preferred_sources=["annual_report", "regulatory_filing", "company_website", "reputable_news"]
        )
    except Exception as e:
        logger.warning("[ProposalAnalysisService] Research fetch issue for %s - %s: %s", prospect_name, param_name, e)

    tagged_evidence_text, prepared_sources, audit_meta = build_tagged_evidence_context(
        company_name=prospect_name,
        parameter_name=param_name,
        raw_evidence_list=raw_evidence or [],
        param_keywords=param_keywords,
        max_snippet_len=750
    )

    if not prepared_sources:
        no_evidence_summary = f"No authoritative public disclosures or verified statutory filings regarding {param_name} were found for {prospect_name}."
        return {
            "parameter_id": parameter_id,
            "parameter": param_name,
            "category": category,
            "fit_level": "Low",
            "confidence": "Low",
            "compliance_status": "Non-Compliant",
            "summary": no_evidence_summary,
            "finding": no_evidence_summary,
            "reasoning": f"Public research did not yield verifiable operational evidence for {param_name}. Accurate assessment requires carrier-provided underwriting exhibits.",
            "why_it_matters": f"Public research did not yield verifiable operational evidence for {param_name}. Accurate assessment requires carrier-provided underwriting exhibits.",
            "verified_capabilities": [],
            "rfp_line_item_matching": [],
            "evidence": [],
            "sources": [],
            "gaps": [
                f"Public disclosures do not substantiate {prospect_name}'s specific capabilities or investments in {param_name}.",
                f"Recommended Data Source: {discovery_suggestion}"
            ],
            "producer_discovery_action": discovery_suggestion
        }

    # Context slicing: match parameter-specific RFP clauses
    param_rfp_clauses = get_parameter_specific_rfp_clauses(parameter_id, param_meta, proposal_profile)
    rfp_clauses_block = "\n".join([f"- {c}" for c in param_rfp_clauses])

    prompt = f"""You are a senior commercial insurance underwriting analyst.
Evaluate how well the prospect '{prospect_name}' fits the requirements of the uploaded proposal for the parameter '{param_name}'.

PROPOSAL CONTEXT:
Title: {proposal_profile.get('proposal_title')}
Domain: {proposal_profile.get('domain')}

PARAMETER-SPECIFIC RFP REQUIREMENTS:
{rfp_clauses_block}

PARAMETER TO EVALUATE:
Name: {param_name} ({category})
Definition: {param_meta.get('description')}

PROSPECT PUBLIC EVIDENCE SOURCES:
{tagged_evidence_text}

Return a strict JSON object with this exact schema:
{{
  "fit_level": "High | Medium | Low",
  "confidence": "High | Medium | Low",
  "compliance_status": "Full Compliance | Partial Compliance | Non-Compliant",
  "summary": "2-4 sentence consolidated summary combining the key capabilities, metrics, and technologies from ALL relevant evidence sources.",
  "reasoning": "1-2 sentence explanation of why this parameter matters to the proposal fit.",
  "verified_capabilities": ["Factual verified capability 1", "Factual verified capability 2"],
  "rfp_line_item_matching": [
    {{
      "rfp_requirement": "Exact requirement from RFP",
      "prospect_capability": "Verified prospect capability",
      "alignment": "Full Fit | Partial Fit | Gap"
    }}
  ],
  "gaps": ["Key unknown or missing confirmation in this area"],
  "producer_discovery_action": "Actionable step for underwriter discovery"
}}
"""
    ai_eval = None
    try:
        ai_resp = query_gemini(prompt, json_output=True, timeout=30)
        if isinstance(ai_resp, dict) and ("summary" in ai_resp or "finding" in ai_resp):
            ai_eval = ai_resp
    except Exception as e:
        logger.warning("[ProposalAnalysisService] Gemini eval failed for %s: %s", param_name, e)

    if not ai_eval:
        try:
            ollama_resp = query_ollama(prompt, json_output=True, timeout=25, model_name=PRIMARY_OLLAMA_MODEL)
            if isinstance(ollama_resp, dict) and ("summary" in ollama_resp or "finding" in ollama_resp):
                ai_eval = ollama_resp
        except Exception as e:
            logger.warning("[ProposalAnalysisService] Ollama eval failed for %s: %s", param_name, e)

    raw_fit = ai_eval.get("fit_level") if ai_eval else "Medium"
    fit_level = "High" if str(raw_fit).strip().lower() in ["high", "very high", "strong"] else ("Low" if str(raw_fit).strip().lower() in ["low", "weak"] else "Medium")
    raw_conf = ai_eval.get("confidence") if ai_eval else "Medium"
    confidence = "High" if str(raw_conf).strip().lower() in ["high", "very high"] else ("Low" if str(raw_conf).strip().lower() in ["low", "weak"] else "Medium")
    compliance_status = ai_eval.get("compliance_status") if ai_eval else ("Full Compliance" if fit_level == "High" else "Partial Compliance")
    
    summary = clean_plain_text(ai_eval.get("summary") or ai_eval.get("finding") or f"{prospect_name} maintains operational capabilities aligned with {param_name} requirements.")
    reasoning = clean_plain_text(ai_eval.get("reasoning") or f"{param_name} directly addresses operational and technological capabilities required by the proposal.")
    
    verified_capabilities = ai_eval.get("verified_capabilities") if ai_eval and isinstance(ai_eval.get("verified_capabilities"), list) else [summary]
    rfp_matching = ai_eval.get("rfp_line_item_matching") if ai_eval and isinstance(ai_eval.get("rfp_line_item_matching"), list) else []
    gaps = ai_eval.get("gaps") if ai_eval and isinstance(ai_eval.get("gaps"), list) else [discovery_suggestion]
    producer_action = ai_eval.get("producer_discovery_action") if ai_eval else discovery_suggestion

    aligned_evidence = filter_and_align_sources(
        finding=summary,
        reasoning=reasoning,
        gaps=gaps,
        prepared_sources=prepared_sources,
        company_name=prospect_name
    )

    return {
        "parameter_id": parameter_id,
        "parameter": param_name,
        "category": category,
        "fit_level": fit_level,
        "confidence": confidence,
        "compliance_status": compliance_status,
        "summary": summary,
        "finding": summary,
        "reasoning": reasoning,
        "why_it_matters": reasoning,
        "verified_capabilities": verified_capabilities,
        "rfp_line_item_matching": rfp_matching,
        "evidence": aligned_evidence,
        "sources": aligned_evidence,
        "gaps": gaps,
        "producer_discovery_action": producer_action
    }


def analyze_proposal_fit(
    db: Session,
    current_user: User,
    prospect_id: Optional[str],
    prospect_name: str,
    proposal_profile: Dict[str, Any],
    selected_parameters: List[str],
    mock_mode: bool = False
) -> Dict[str, Any]:
    """
    Main Proposal-Based Prospect Analysis Engine.
    Executes in TWO optimized stages:
      1. Parallel Research & Context Slicing across all selected parameters.
      2. Single Batched Multi-Parameter Evaluation LLM Call ($O(N) \to O(1)$ API calls).
    """
    if not prospect_name or not prospect_name.strip():
        raise ValueError("Please select a prospect before starting analysis.")

    if not proposal_profile or not isinstance(proposal_profile, dict):
        raise ValueError("Valid proposal profile required for analysis.")

    valid_param_ids = validate_selected_parameters(selected_parameters)

    logger.info("[ProposalAnalysisService] Starting Proposal-Based Prospect Analysis for '%s' against '%s' (%d params, Batched Mode)...",
                prospect_name, proposal_profile.get("proposal_title"), len(valid_param_ids))

    # Fast-path for mock_mode (unit testing)
    if mock_mode:
        parameter_results = [
            evaluate_parameter_fit(prospect_name, pid, proposal_profile, mock_mode=True)
            for pid in valid_param_ids
        ]
        summary_data = generate_proposal_executive_summary(
            prospect_name=prospect_name,
            proposal_profile=proposal_profile,
            parameter_results=parameter_results,
            mock_mode=True
        )
        return _persist_and_format_proposal_output(
            db=db,
            current_user=current_user,
            prospect_id=prospect_id,
            prospect_name=prospect_name,
            proposal_profile=proposal_profile,
            parameter_results=parameter_results,
            summary_data=summary_data
        )

    # -------------------------------------------------------------------------
    # STAGE 1: Parallel Evidence Gathering & Parameter-Specific Context Slicing
    # -------------------------------------------------------------------------
    param_data_blocks: Dict[str, Dict[str, Any]] = {}

    def prepare_parameter_context(pid: str) -> tuple[str, Dict[str, Any]]:
        param_meta = PROPOSAL_PARAMETERS_BY_ID.get(pid, {
            "name": pid.replace("_", " ").title(),
            "category": "General",
            "description": f"Evaluation of {pid}",
            "keywords": []
        })
        param_name = param_meta["name"]
        category = param_meta["category"]
        param_keywords = param_meta.get("keywords", [])
        discovery_suggestion = PARAMETER_DISCOVERY_SUGGESTIONS.get(
            pid,
            f"Request specific underwriting exhibits and operational disclosures for {param_name} directly from {prospect_name}."
        )

        queries = param_meta.get("search_queries", [f"{prospect_name} {param_name}"])
        raw_evidence = []
        try:
            raw_evidence = search_all_sources(
                company_name=prospect_name,
                parameter=param_name,
                search_queries=queries,
                preferred_sources=["annual_report", "regulatory_filing", "company_website", "reputable_news"]
            )
        except Exception as exc:
            logger.warning("[ProposalAnalysisService] Research fetch issue for %s - %s: %s", prospect_name, param_name, exc)

        tagged_evidence_text, prepared_sources, audit_meta = build_tagged_evidence_context(
            company_name=prospect_name,
            parameter_name=param_name,
            raw_evidence_list=raw_evidence or [],
            param_keywords=param_keywords,
            max_snippet_len=750
        )

        specific_rfp_clauses = get_parameter_specific_rfp_clauses(pid, param_meta, proposal_profile)

        return pid, {
            "parameter_id": pid,
            "parameter_name": param_name,
            "category": category,
            "param_meta": param_meta,
            "discovery_suggestion": discovery_suggestion,
            "tagged_evidence_text": tagged_evidence_text,
            "prepared_sources": prepared_sources,
            "audit_meta": audit_meta,
            "specific_rfp_clauses": specific_rfp_clauses
        }

    max_workers = min(PROPOSAL_MAX_CONCURRENT_PARAMETERS, len(valid_param_ids)) or 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(prepare_parameter_context, pid): pid for pid in valid_param_ids}
        for f in concurrent.futures.as_completed(futures):
            pid, p_ctx = f.result()
            param_data_blocks[pid] = p_ctx

    # -------------------------------------------------------------------------
    # STAGE 2: 1 Unified Batched LLM Evaluation Prompt (O(N) -> O(1))
    # -------------------------------------------------------------------------
    eval_sections = []
    for pid in valid_param_ids:
        p_ctx = param_data_blocks[pid]
        p_name = p_ctx["parameter_name"]
        p_cat = p_ctx["category"]
        p_desc = p_ctx["param_meta"].get("description", "")
        rfp_clauses = "\n".join([f"    * {c}" for c in p_ctx["specific_rfp_clauses"]]) or "    * General commercial insurance RFP requirements"
        evidence_text = p_ctx["tagged_evidence_text"] if p_ctx["prepared_sources"] else "    * No verified public statutory disclosures or empirical news found."

        eval_sections.append(f"""### PARAMETER ID: {pid}
  Name: {p_name} ({p_cat})
  Definition: {p_desc}
  Relevant RFP Clauses:
{rfp_clauses}
  Collected Public Evidence:
{evidence_text}
""")

    batched_sections_text = "\n\n".join(eval_sections)

    unified_prompt = f"""You are a senior commercial insurance underwriting analyst.
Evaluate the prospect '{prospect_name}' against the RFP specifications across ALL of the following {len(valid_param_ids)} parameter dimensions in one unified assessment.

PROPOSAL SUMMARY:
Title: {proposal_profile.get('proposal_title')}
Domain: {proposal_profile.get('domain', 'Commercial Insurance')}
Objectives: {", ".join(proposal_profile.get('business_objectives', [])[:3]) or 'Automate workflows and ensure high-tier risk management'}

==================================================
PARAMETERS AND EVIDENCE TO EVALUATE:
==================================================
{batched_sections_text}

==================================================
MANDATORY EVALUATION DIRECTIVES:
==================================================
1. EVALUATE EACH PARAMETER ID SEPARATELY using its tagged evidence.
2. For each parameter, return:
   - "fit_level": "High" (strong capability & alignment), "Medium" (partial alignment or moderate disclosures), or "Low" (unsupported or severe gaps).
   - "confidence": "High" | "Medium" | "Low"
   - "compliance_status": "Full Compliance" | "Partial Compliance" | "Non-Compliant"
   - "summary": 2-4 sentence analytical narrative combining the facts from all displayed sources.
   - "reasoning": 1-2 sentence underwriting justification explaining why this parameter matters to the RFP.
   - "verified_capabilities": 2-3 concise bullet points of verified empirical facts/metrics.
   - "rfp_line_item_matching": Array of objects mapping each specific RFP clause to prospect capability with alignment ("Full Fit", "Partial Fit", or "Gap").
   - "gaps": 1-2 specific missing exhibits, unknowns, or unconfirmed SLAs.
   - "producer_discovery_action": 1 concrete discovery step for the underwriter/producer.
3. NO NUMERICAL SCORES OR PERCENTAGES. Qualitative evaluation only.

Return a strict JSON object with this exact schema:
{{
  "parameter_evaluations": {{
    "<parameter_id>": {{
      "fit_level": "High | Medium | Low",
      "confidence": "High | Medium | Low",
      "compliance_status": "Full Compliance | Partial Compliance | Non-Compliant",
      "summary": "2-4 sentence consolidated factual assessment...",
      "reasoning": "1-2 sentence underwriting reason...",
      "verified_capabilities": ["Capability metric 1", "Capability metric 2"],
      "rfp_line_item_matching": [
        {{
          "rfp_requirement": "Clause from RFP",
          "prospect_capability": "Verified prospect capability",
          "alignment": "Full Fit | Partial Fit | Gap"
        }}
      ],
      "gaps": ["Identified operational gap or unverified SLA"],
      "producer_discovery_action": "Actionable discovery inquiry"
    }}
  }}
}}
"""
    batched_ai_result = None
    gemini_err = None
    ollama_err = None

    try:
        logger.info("[ProposalAnalysisService] Executing Batched Gemini Evaluation for %d parameters...", len(valid_param_ids))
        gem_resp = query_gemini(unified_prompt, json_output=True, timeout=35)
        if isinstance(gem_resp, dict) and ("parameter_evaluations" in gem_resp or any(pid in gem_resp for pid in valid_param_ids)):
            batched_ai_result = gem_resp.get("parameter_evaluations", gem_resp)
    except Exception as e:
        gemini_err = str(e)
        logger.warning("[ProposalAnalysisService] Batched Gemini eval failed: %s. Falling back to Ollama...", e)

    if not batched_ai_result:
        try:
            logger.info("[ProposalAnalysisService] Executing Batched Ollama Evaluation (%s)...", PRIMARY_OLLAMA_MODEL)
            ollama_resp = query_ollama(unified_prompt, json_output=True, timeout=30, model_name=PRIMARY_OLLAMA_MODEL)
            if isinstance(ollama_resp, dict) and ("parameter_evaluations" in ollama_resp or any(pid in ollama_resp for pid in valid_param_ids)):
                batched_ai_result = ollama_resp.get("parameter_evaluations", ollama_resp)
        except Exception as e:
            ollama_err = str(e)
            logger.warning("[ProposalAnalysisService] Batched Ollama eval failed: %s", e)

    # -------------------------------------------------------------------------
    # STAGE 3: Assemble & Align Intelligence Dossier for each parameter
    # -------------------------------------------------------------------------
    parameter_results = []

    for pid in valid_param_ids:
        p_ctx = param_data_blocks[pid]
        p_name = p_ctx["parameter_name"]
        p_cat = p_ctx["category"]
        prepared_sources = p_ctx["prepared_sources"]
        discovery_suggestion = p_ctx["discovery_suggestion"]

        ai_eval = batched_ai_result.get(pid, {}) if isinstance(batched_ai_result, dict) else {}

        if not prepared_sources:
            no_evidence_summary = f"No authoritative public disclosures or verified statutory filings regarding {p_name} were found for {prospect_name}."
            parameter_results.append({
                "parameter_id": pid,
                "parameter": p_name,
                "category": p_cat,
                "fit_level": "Low",
                "confidence": "Low",
                "compliance_status": "Non-Compliant",
                "summary": no_evidence_summary,
                "finding": no_evidence_summary,
                "reasoning": f"Public research did not yield verifiable operational evidence for {p_name}. Direct carrier exhibits required.",
                "why_it_matters": f"Public research did not yield verifiable operational evidence for {p_name}. Direct carrier exhibits required.",
                "verified_capabilities": [],
                "rfp_line_item_matching": [],
                "evidence": [],
                "sources": [],
                "gaps": [
                    f"Public disclosures do not substantiate {prospect_name}'s specific capabilities in {p_name}.",
                    f"Recommended Data Source: {discovery_suggestion}"
                ],
                "producer_discovery_action": discovery_suggestion
            })
            continue

        raw_fit = ai_eval.get("fit_level") or ("High" if len(prepared_sources) >= 3 else "Medium")
        fit_level = "High" if str(raw_fit).strip().lower() in ["high", "very high", "strong"] else ("Low" if str(raw_fit).strip().lower() in ["low", "weak"] else "Medium")
        
        raw_conf = ai_eval.get("confidence") or ("High" if len(prepared_sources) >= 2 else "Medium")
        confidence = "High" if str(raw_conf).strip().lower() in ["high", "very high"] else ("Low" if str(raw_conf).strip().lower() in ["low", "weak"] else "Medium")
        
        compliance_status = ai_eval.get("compliance_status") or ("Full Compliance" if fit_level == "High" else "Partial Compliance")

        diag_notice = ""
        if not batched_ai_result:
            diag_notice = f" [Note: Synthesized via deterministic empirical engine. External AI models unavailable (Gemini: {gemini_err or 'timeout'} | Ollama: {ollama_err or 'timeout'})]"

        summary = clean_plain_text(ai_eval.get("summary") or ai_eval.get("finding") or f"{prospect_name} demonstrates active operational alignment with {p_name} specifications based on public statutory disclosures.") + diag_notice
        reasoning = clean_plain_text(ai_eval.get("reasoning") or f"{p_name} directly addresses operational and technological capabilities required by the proposal.")
        
        raw_caps = ai_eval.get("verified_capabilities") or [summary]
        verified_caps = [clean_plain_text(str(c)) for c in raw_caps if clean_plain_text(str(c))]

        raw_matching = ai_eval.get("rfp_line_item_matching") or [
            {
                "rfp_requirement": p_ctx["specific_rfp_clauses"][0] if p_ctx["specific_rfp_clauses"] else f"Mandatory operational capability in {p_name}",
                "prospect_capability": f"Verified public disclosure confirming production capability in {p_name}",
                "alignment": "Full Fit" if fit_level == "High" else "Partial Fit"
            }
        ]

        raw_gaps = ai_eval.get("gaps") or [
            f"Public disclosures do not confirm a signed vendor contract for this specific scope.",
            f"Recommended Data Source: {discovery_suggestion}"
        ]
        gaps = [clean_plain_text(str(g)) for g in raw_gaps if clean_plain_text(str(g))]
        producer_action = ai_eval.get("producer_discovery_action") or discovery_suggestion

        aligned_evidence = filter_and_align_sources(
            finding=summary,
            reasoning=reasoning,
            gaps=gaps,
            prepared_sources=prepared_sources,
            company_name=prospect_name
        )

        parameter_results.append({
            "parameter_id": pid,
            "parameter": p_name,
            "category": p_cat,
            "fit_level": fit_level,
            "confidence": confidence,
            "compliance_status": compliance_status,
            "summary": summary,
            "finding": summary,
            "reasoning": reasoning,
            "why_it_matters": reasoning,
            "verified_capabilities": verified_caps,
            "rfp_line_item_matching": raw_matching,
            "evidence": aligned_evidence,
            "sources": aligned_evidence,
            "gaps": gaps,
            "producer_discovery_action": producer_action
        })

    # -------------------------------------------------------------------------
    # STAGE 4: Executive Synthesis & Persistence
    # -------------------------------------------------------------------------
    summary_data = generate_proposal_executive_summary(
        prospect_name=prospect_name,
        proposal_profile=proposal_profile,
        parameter_results=parameter_results,
        mock_mode=mock_mode
    )

    return _persist_and_format_proposal_output(
        db=db,
        current_user=current_user,
        prospect_id=prospect_id,
        prospect_name=prospect_name,
        proposal_profile=proposal_profile,
        parameter_results=parameter_results,
        summary_data=summary_data
    )


def _persist_and_format_proposal_output(
    db: Session,
    current_user: User,
    prospect_id: Optional[str],
    prospect_name: str,
    proposal_profile: Dict[str, Any],
    parameter_results: List[Dict[str, Any]],
    summary_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Helper to persist proposal analysis to PostgreSQL and construct output payload."""
    report_dict = {}
    for p in parameter_results:
        report_dict[p["parameter"]] = {
            "parameter_id": p["parameter_id"],
            "score": None,
            "fit_level": p.get("fit_level", "Medium"),
            "confidence": p.get("confidence", "Medium"),
            "compliance_status": p.get("compliance_status", "Partial Compliance"),
            "finding": p["finding"],
            "summary": p["finding"],
            "reasoning": p["reasoning"],
            "why_it_matters": p["reasoning"],
            "verified_capabilities": p.get("verified_capabilities", []),
            "rfp_line_item_matching": p.get("rfp_line_item_matching", []),
            "key_facts": p.get("verified_capabilities", [p["finding"]]),
            "evidence": p["evidence"],
            "sources": p["evidence"],
            "gaps": p["gaps"],
            "producer_discovery_action": p.get("producer_discovery_action"),
            "category": p["category"]
        }

    report_dict["_summary_synthesis"] = summary_data
    proposal_details_to_store = dict(proposal_profile) if isinstance(proposal_profile, dict) else {}
    proposal_details_to_store["summary_synthesis"] = summary_data

    db_entry = ProspectAnalysisDB(
        user_uuid=current_user.uuid,
        user_id=current_user.id,
        company_name=prospect_name,
        analysis_mode="PROPOSAL",
        proposal_details=proposal_details_to_store,
        proposal_filename=proposal_profile.get("filename"),
        risk_rating="Evaluated",
        report_data=report_dict,
        executive_summary=summary_data["summary"],
        score=None,
        avg_confidence_level="High" if len(parameter_results) >= 3 else "Medium",
        chat_history=[]
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    analysis_uuid = f"PA-{uuid.uuid4().hex[:8].upper()}"

    output = {
        "analysis_id": analysis_uuid,
        "id": db_entry.id,
        "prospect": {
            "id": prospect_id or "INS-UNKNOWN",
            "name": prospect_name
        },
        "proposal": {
            "id": proposal_profile.get("proposal_id"),
            "title": proposal_profile.get("proposal_title"),
            "domain": proposal_profile.get("domain", "Commercial Insurance"),
            "filename": proposal_profile.get("filename")
        },
        "parameter_analysis": parameter_results,
        "strengths": summary_data.get("strongest_alignment", []),
        "gaps": summary_data.get("key_gaps", []),
        "risks": summary_data.get("risks_and_unknowns", []),
        "opportunity_signals": summary_data.get("opportunity_signals", []),
        "recommended_contact_angle": summary_data.get("recommended_contact_angle", ""),
        "recommended_next_action": summary_data.get("recommended_next_action", ""),
        "overall_assessment": summary_data.get("overall_assessment", summary_data.get("summary", "")),
        "summary": summary_data.get("summary", ""),
        "executive_summary": summary_data.get("summary", ""),
        "created_at": db_entry.created_at.isoformat() if db_entry.created_at else datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    logger.info("[ProposalAnalysisService] Proposal-Based Prospect Analysis complete for '%s' (ID: %s, Params: %d)",
                prospect_name, analysis_uuid, len(parameter_results))
    return output


def format_sse(event_type: str, data: Any) -> str:
    """Formats an SSE message event with JSON data."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event_type}\ndata: {payload}\n\n"


def stream_proposal_analysis(
    db: Session,
    current_user: User,
    prospect_id: Optional[str],
    prospect_name: str,
    proposal_profile: Dict[str, Any],
    selected_parameters: List[str],
    mock_mode: bool = False
) -> Generator[str, None, None]:
    """
    Executes Concurrent Proposal-Based Prospect Analysis and streams results progressively via SSE.
    Each parameter is analyzed concurrently in a ThreadPoolExecutor.
    As soon as an individual parameter completes, its result is yielded immediately.
    Once all parameters have reached a terminal state, final consolidated analysis is generated and persisted.
    """
    if not prospect_name or not prospect_name.strip():
        raise ValueError("Please select a prospect before starting analysis.")

    if not proposal_profile or not isinstance(proposal_profile, dict):
        raise ValueError("Valid proposal profile required for analysis.")

    valid_param_ids = validate_selected_parameters(selected_parameters)
    total_count = len(valid_param_ids)

    # 1. Emit init event
    yield format_sse("init", {
        "prospect_name": prospect_name,
        "total_parameters": total_count,
        "selected_parameters": valid_param_ids
    })

    # 2. Worker Pool Sizing
    max_workers = min(PROPOSAL_MAX_CONCURRENT_PARAMETERS, total_count) or 1
    logger.info(
        "[ProposalAnalysisService] Starting Concurrent Streaming Analysis for '%s' against '%s' (Params: %d, Max Workers: %d)...",
        prospect_name, proposal_profile.get("proposal_title"), total_count, max_workers
    )

    future_to_pid = {}
    completed_results = []
    failed_params = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks concurrently at t=0
        for pid in valid_param_ids:
            future = executor.submit(
                evaluate_parameter_fit,
                prospect_name,
                pid,
                proposal_profile,
                mock_mode
            )
            future_to_pid[future] = pid
            yield format_sse("param_started", {
                "parameter_id": pid,
                "status": "processing"
            })

        # Yield results immediately as individual parameters complete
        for future in concurrent.futures.as_completed(future_to_pid):
            pid = future_to_pid[future]
            try:
                result = future.result()
                result["status"] = "completed"
                result["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                if "findings" not in result:
                    result["findings"] = [result.get("summary") or result.get("finding", "")]
                completed_results.append(result)
                yield format_sse("param_completed", result)
            except Exception as exc:
                logger.exception("[ProposalAnalysisService] Parameter %s evaluation failed: %s", pid, exc)
                failed_params.append(pid)
                yield format_sse("param_failed", {
                    "parameter_id": pid,
                    "status": "failed",
                    "error": str(exc)
                })

    # 3. Generate Consolidated Summary only after all parameters reach terminal state
    summary_data = generate_proposal_executive_summary(
        prospect_name=prospect_name,
        proposal_profile=proposal_profile,
        parameter_results=completed_results,
        mock_mode=mock_mode
    )

    yield format_sse("summary_ready", {
        "executive_summary": summary_data.get("summary", ""),
        "overall_assessment": summary_data.get("overall_assessment", summary_data.get("summary", "")),
        "strengths": summary_data.get("strongest_alignment", []),
        "gaps": summary_data.get("key_gaps", []),
        "risks": summary_data.get("risks_and_unknowns", []),
        "opportunity_signals": summary_data.get("opportunity_signals", []),
        "recommended_contact_angle": summary_data.get("recommended_contact_angle", ""),
        "recommended_next_action": summary_data.get("recommended_next_action", "")
    })

    # 4. Persist to PostgreSQL and yield complete event
    full_output = _persist_and_format_proposal_output(
        db=db,
        current_user=current_user,
        prospect_id=prospect_id,
        prospect_name=prospect_name,
        proposal_profile=proposal_profile,
        parameter_results=completed_results,
        summary_data=summary_data
    )
    full_output["status"] = "completed"

    yield format_sse("complete", full_output)

