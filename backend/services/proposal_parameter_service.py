"""
Proposal Parameter Service for Proposal-Based Prospect Analysis.
Provides the catalog of proposal-analysis parameters, computes dynamic recommendations
and validates user selections based on extracted proposal requirements.
"""

from typing import List, Dict, Any, Optional
import logging

from config.proposal_analysis_config import (
    PROPOSAL_PARAMETERS_CATALOG,
    PROPOSAL_PARAMETERS_BY_ID,
)
from services.proposal_retrieval_service import (
    extract_chunks_from_profile,
    retrieve_authoritative_catalog_excerpts
)

logger = logging.getLogger(__name__)


def get_parameter_catalog() -> List[Dict[str, Any]]:
    """
    Returns the complete catalog of proposal-analysis parameters.
    """
    return [dict(p) for p in PROPOSAL_PARAMETERS_CATALOG]


import json
from ai.gemini import query_gemini
from ai.ollama import query_ollama, PRIMARY_OLLAMA_MODEL

_RECOMMENDATION_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def _make_profile_cache_key(profile: Dict[str, Any]) -> str:
    title = str(profile.get("proposal_title") or "").strip().lower()
    pid = str(profile.get("proposal_id") or "").strip()
    reqs = (
        (profile.get("functional_requirements") or []) +
        (profile.get("requirements") or []) +
        (profile.get("capabilities") or [])
    )
    req_tuple = tuple(sorted([str(r).strip().lower() for r in reqs]))
    return f"{pid}:{title}:{hash(req_tuple)}"


def clear_recommendation_cache():
    """Clears the evaluation cache."""
    _RECOMMENDATION_CACHE.clear()


def _extract_evaluations_list(ai_resp: Any) -> Optional[List[Dict[str, Any]]]:
    """
    Extracts a list of parameter evaluation dictionaries from various LLM response formats:
    - Dict with key 'parameter_evaluations', 'evaluations', 'parameters', 'results'
    - Direct list of dicts
    - Dict mapping parameter IDs to evaluation objects
    """
    if not ai_resp:
        return None

    # 1. Direct list of dicts
    if isinstance(ai_resp, list) and len(ai_resp) > 0 and isinstance(ai_resp[0], dict):
        return ai_resp

    # 2. Dict containing a list key
    if isinstance(ai_resp, dict):
        for key in ["parameter_evaluations", "evaluations", "parameters", "results", "data", "parameter_analysis"]:
            val = ai_resp.get(key)
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                return val

        # 3. Dict keyed by parameter_id e.g. {"claims_relevance": {"relevance_score": 90, ...}}
        items = []
        for pid, data in ai_resp.items():
            if isinstance(data, dict):
                entry = dict(data)
                if "parameter_id" not in entry:
                    entry["parameter_id"] = pid
                items.append(entry)
        if len(items) >= 5:
            return items

    return None




def evaluate_all_parameters(proposal_profile: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Evaluates ALL 15 parameters in the catalog against the extracted Proposal Profile
    using the Dual-Branch Architecture:
    - Branch 1 (Contextual Profile): High-level domain, summary, business objectives, products
    - Branch 2 (Authoritative Chunks): Full RFP chunks indexed with BM25/Dense retrieval
    """
    if not proposal_profile:
        return []

    cache_key = _make_profile_cache_key(proposal_profile)
    if cache_key in _RECOMMENDATION_CACHE:
        return [dict(x) for x in _RECOMMENDATION_CACHE[cache_key]]

    title = str(proposal_profile.get("proposal_title") or "Insurance Proposal / RFP")
    domain = str(proposal_profile.get("domain") or "Commercial Insurance")
    summary = str(proposal_profile.get("summary") or "")
    insurance_products = proposal_profile.get("insurance_products") or []
    business_objectives = proposal_profile.get("business_objectives") or proposal_profile.get("objectives") or []
    business_problems = proposal_profile.get("business_problems") or []
    functional_reqs = proposal_profile.get("functional_requirements") or proposal_profile.get("requirements") or []
    tech_reqs = proposal_profile.get("technology_requirements") or []
    ai_ml_reqs = proposal_profile.get("ai_ml_requirements") or []
    data_reqs = proposal_profile.get("data_requirements") or []
    integration_reqs = proposal_profile.get("integration_requirements") or []
    regulatory_reqs = proposal_profile.get("regulatory_requirements") or []
    impl_reqs = proposal_profile.get("implementation_requirements") or []
    eval_criteria = proposal_profile.get("evaluation_criteria") or []
    eval_weights = proposal_profile.get("evaluation_weights") or []

    # Branch 2: Authoritative Chunk Extraction & Dense/BM25 Retrieval
    authoritative_chunks = extract_chunks_from_profile(proposal_profile)
    retrieval_map = retrieve_authoritative_catalog_excerpts(authoritative_chunks, PROPOSAL_PARAMETERS_CATALOG)

    catalog_summary = []
    for p in PROPOSAL_PARAMETERS_CATALOG:
        ret_data = retrieval_map.get(p["id"], {})
        catalog_summary.append({
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "description": p["description"],
            "keywords": p.get("keywords", []),
            "retrieved_rfp_excerpts": ret_data.get("excerpts", [])[:3]
        })

    # AI-Powered Dynamic Parameter Evaluation with Dual-Branch inputs
    llm_prompt = f"""You are a senior insurance underwriting and technology RFP evaluation specialist.
Carefully analyze the following uploaded RFP Profile using Dual-Branch Intelligence:
- BRANCH 1 (CONTEXTUAL PROFILE): High-level title, business domain, objectives, and problem statement.
- BRANCH 2 (AUTHORITATIVE RFP EXCERPTS): Verbatim requirement clauses and specifications retrieved across the full document.

PROPOSAL CONTEXTUAL PROFILE:
Title: {title}
Domain: {domain}
Summary: {summary}
Insurance Products: {json.dumps(insurance_products)}
Business Objectives: {json.dumps(business_objectives)}
Business Problems: {json.dumps(business_problems)}
Functional Requirements Sample: {json.dumps(functional_reqs[:12])}
Technology Requirements: {json.dumps(tech_reqs[:6])}
AI/ML Requirements: {json.dumps(ai_ml_reqs[:6])}
Evaluation Criteria: {json.dumps(eval_criteria[:6])}
Evaluation Weights: {json.dumps(eval_weights)}

CATALOG OF 15 PARAMETERS WITH AUTHORITATIVE RETRIEVED RFP EXCERPTS:
{json.dumps(catalog_summary, indent=2)}

CRITICAL EVALUATION RULES:
1. Evaluate ALL 15 parameters in the catalog. Do NOT skip any parameter.
2. For each parameter provide:
   - "parameter_id": exact id from catalog
   - "parameter": exact name from catalog
   - "relevance_score": integer from 0 to 100 representing direct relevance to this specific RFP
   - "recommendation": "recommended" if relevance_score >= 60 and directly tied to RFP requirements, otherwise "not_recommended"
   - "reason": 1-2 clear, specific sentences explaining why it is or is not recommended based on this RFP's scope.
   - "rfp_evidence": list of direct quotes or requirement statements from the RFP (prioritize the retrieved authoritative excerpts, empty list if not recommended)
   - "confidence": "High", "Medium", or "Low"
3. NO HALLUCINATIONS: Ground recommendations directly in the retrieved authoritative excerpts and the contextual profile domain.
4. When a parameter has authoritative retrieved clauses, score it high (>=70) and cite the exact quotes in rfp_evidence.
5. If no RFP evidence exists and the domain does not demand it, score it low (<40) and set recommendation to "not_recommended".
6. If Evaluation Weights are present in the RFP, prioritize weighted dimensions accordingly.

Return a strict JSON object with this structure:
{{
  "parameter_evaluations": [
    {{
      "parameter_id": "claims_relevance",
      "parameter": "Claims Relevance",
      "relevance_score": 92,
      "recommendation": "recommended",
      "reason": "Claims intake, triage, and automation are explicitly listed as primary functional deliverables in the RFP scope.",
      "rfp_evidence": ["Digital claims intake", "Automated claims triage"],
      "confidence": "High"
    }}
  ]
}}
"""

    ai_evaluations: Optional[List[Dict[str, Any]]] = None

    # Step A: Attempt Gemini with 35s timeout
    try:
        ai_resp = query_gemini(llm_prompt, json_output=True, timeout=35)
        evals = _extract_evaluations_list(ai_resp)
        if evals and len(evals) >= 5:
            ai_evaluations = evals
            logger.info("[ProposalParameterService] Gemini successfully evaluated %d parameters for '%s'", len(evals), title)
    except Exception as e:
        logger.warning("[ProposalParameterService] Gemini evaluation skipped/failed: %s", e)

    # Step B: Attempt Ollama if Gemini was unavailable or returned unusable output
    if not ai_evaluations:
        try:
            fast_model = "qwen2.5:1.5b" if "qwen2.5:1.5b" in (PRIMARY_OLLAMA_MODEL + " qwen2.5:1.5b") else PRIMARY_OLLAMA_MODEL
            ollama_resp = query_ollama(llm_prompt, json_output=True, timeout=35, model_name=fast_model)
            evals = _extract_evaluations_list(ollama_resp)
            if evals and len(evals) >= 5:
                ai_evaluations = evals
                logger.info("[ProposalParameterService] Ollama successfully evaluated %d parameters for '%s'", len(evals), title)
        except Exception as e:
            logger.warning("[ProposalParameterService] Ollama evaluation skipped/failed: %s", e)

    # Fail explicitly if AI services are unavailable
    if not ai_evaluations:
        logger.error("[ProposalParameterService] AI services (Gemini/Ollama) are unavailable to evaluate parameters for '%s'", title)
        raise RuntimeError(
            "AI services (Gemini/Ollama) are currently unavailable to evaluate proposal parameters. "
            "Please check API keys and connectivity."
        )

    normalized_evals = []
    seen_ids = set()
    for item in ai_evaluations:
        pid = item.get("parameter_id")
        if pid in PROPOSAL_PARAMETERS_BY_ID and pid not in seen_ids:
            seen_ids.add(pid)
            cat_meta = PROPOSAL_PARAMETERS_BY_ID[pid]
            rec = item.get("recommendation", "not_recommended")
            score = int(item.get("relevance_score", 15))
            evidence = item.get("rfp_evidence") or []
            if not isinstance(evidence, list):
                evidence = [str(evidence)]
            
            # Enrich evidence from authoritative retrieval if AI didn't supply direct quotes
            if (rec == "recommended" or score >= 60) and not evidence:
                evidence = retrieval_map.get(pid, {}).get("excerpts", [])[:3]

            normalized_evals.append({
                "parameter_id": pid,
                "parameter": cat_meta["name"],
                "relevance_score": score,
                "recommendation": "recommended" if (rec == "recommended" or score >= 60) else "not_recommended",
                "reason": item.get("reason") or (
                    f"{cat_meta['name']} aligns directly with the RFP specifications."
                    if score >= 60 else
                    f"The uploaded RFP does not identify {cat_meta['name'].lower()} as a material requirement."
                ),
                "rfp_evidence": evidence if score >= 60 else [],
                "confidence": item.get("confidence") or ("High" if score >= 75 else ("Medium" if score >= 50 else "Low"))
            })

    for p in PROPOSAL_PARAMETERS_CATALOG:
        if p["id"] not in seen_ids:
            normalized_evals.append({
                "parameter_id": p["id"],
                "parameter": p["name"],
                "relevance_score": 15,
                "recommendation": "not_recommended",
                "reason": f"The uploaded RFP does not identify {p['name'].lower()} as a material business requirement.",
                "rfp_evidence": [],
                "confidence": "Low"
            })

    id_to_eval = {e["parameter_id"]: e for e in normalized_evals}
    result = [id_to_eval[p["id"]] for p in PROPOSAL_PARAMETERS_CATALOG if p["id"] in id_to_eval]
    _RECOMMENDATION_CACHE[cache_key] = result
    return result


def recommend_parameters(proposal_profile: Optional[Dict[str, Any]]) -> List[str]:
    """
    Returns only the parameter IDs dynamically recommended for the given Proposal Profile.
    Returns an EMPTY list if no profile is provided (Step 1 requirement).
    """
    if not proposal_profile:
        return []

    evaluations = evaluate_all_parameters(proposal_profile)
    return [p["parameter_id"] for p in evaluations if p.get("recommendation") == "recommended"]


def validate_selected_parameters(selected_ids: List[str]) -> List[str]:
    """
    Validates user-selected parameter IDs against the known catalog.
    Logs catalog count, selected count/IDs, validated count, and rejected IDs.
    Raises ValueError if no parameters or only invalid parameters are selected.
    """
    if not selected_ids or not isinstance(selected_ids, list):
        raise ValueError("Please select at least one analysis parameter.")

    total_catalog_count = len(PROPOSAL_PARAMETERS_CATALOG)
    valid_ids = [pid for pid in selected_ids if pid in PROPOSAL_PARAMETERS_BY_ID]
    rejected_ids = [pid for pid in selected_ids if pid not in PROPOSAL_PARAMETERS_BY_ID]

    logger.info(
        "[ProposalParameterService] Parameter Validation Audit: "
        "TOTAL_CATALOG_PARAMETERS=%d, SELECTED_PARAMETERS=%d, "
        "SELECTED_PARAM_IDS=%s, VALIDATED_PARAMETERS=%d, REJECTED_PARAM_IDS=%s",
        total_catalog_count,
        len(selected_ids),
        selected_ids,
        len(valid_ids),
        rejected_ids
    )

    if rejected_ids:
        logger.warning(
            "[ProposalParameterService] Encountered %d rejected parameter IDs not found in catalog: %s",
            len(rejected_ids),
            rejected_ids
        )

    if not valid_ids:
        raise ValueError("Please select at least one valid analysis parameter from the catalog.")

    return valid_ids

