import logging
import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from ai.ollama import query_ollama
from services.prospect_service import resolve_prospect
from services.intent_service import is_general_chat_greeting, is_unsupported_request, detect_parameter_match

logger = logging.getLogger(__name__)


class ProspectContextResolutionResult(BaseModel):
    """
    Structured outcome of the generic prospect context resolution pipeline.
    Determines whether a user query refers to the active prospect, names a different prospect,
    is a multi-prospect comparison, or refers to no prospect/general chat.
    """
    intent: str = Field(default="prospect_analysis", description="prospect_analysis | prospect_comparison | general_chat | unsupported")
    mentioned_prospect: Optional[str] = None
    mentioned_prospect_id: Optional[str] = None
    prospect_reference: str = Field(..., description="active_prospect | different_prospect | comparative | no_prospect | ambiguous")
    comparison_prospects: List[str] = Field(default_factory=list)
    active_prospect: Optional[str] = None
    active_prospect_id: Optional[str] = None
    requested_parameter: Optional[str] = None
    requires_switch_confirmation: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    candidates: List[Dict[str, str]] = Field(default_factory=list)
    reason: str = ""


def _extract_company_with_ollama(
    user_message: str,
    active_prospect: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uses local Ollama to semantically extract any mentioned company names and requested parameter.
    Operates strictly as an extraction assistant; does not modify state.
    """
    prompt = f"""You are a prospect-context resolver.

Your task is to determine which prospect/company the user's latest request refers to.

Current Active Prospect: "{active_prospect or 'None'}"
User Message: "{user_message}"

Instructions:
1. Extract any company or organization name explicitly mentioned in the user message.
2. Determine whether the user:
   - refers to the active prospect ("active_prospect")
   - explicitly refers to a different prospect ("different_prospect")
   - compares multiple prospects ("comparative")
   - does not specify any prospect / general ("no_prospect")
   - is ambiguous ("ambiguous")
3. Extract the requested underwriting parameter separately from company names.

Return ONLY valid JSON matching this schema:
{{
  "mentioned_prospect": "<extracted company name or null>",
  "prospect_reference": "active_prospect" | "different_prospect" | "comparative" | "no_prospect" | "ambiguous",
  "comparison_prospects": ["<prospect1>", "<prospect2>"],
  "requested_parameter": "<extracted parameter or null>",
  "confidence": 0.95
}}
"""
    try:
        res = query_ollama(prompt, json_output=True, timeout=2)
        if isinstance(res, dict):
            return res
    except Exception as exc:
        logger.debug("Ollama context extraction notice: %s", exc)
    return {}


def _extract_all_mentioned_prospects(text: str) -> List[Dict[str, Any]]:
    """
    Scans text from longest to shortest token sequences to extract ALL distinct valid insurance prospects mentioned.
    Uses non-overlapping token index tracking to prevent sub-phrase collisions (e.g. 'Life Insurance' inside 'SBI Life Insurance').
    """
    cleaned_text = re.sub(r"['’]s\b", "", text.strip(), flags=re.IGNORECASE)
    if not cleaned_text:
        return []

    words = re.findall(r'[A-Za-z0-9&.-]+', cleaned_text)
    matched_by_id = {}
    consumed_indices = set()

    for n in range(min(5, len(words)), 0, -1):
        for i in range(len(words) - n + 1):
            span_indices = set(range(i, i + n))
            if span_indices.intersection(consumed_indices):
                continue

            phrase = " ".join(words[i:i+n])
            if n == 1 and phrase.lower() in ["tell", "about", "company", "scale", "the", "its", "what", "is", "of", "for", "and", "growth", "risk", "life", "insurance", "performance", "strength", "between", "vs", "versus", "compare", "who"]:
                continue

            p_match, p_cands, p_status = resolve_prospect(phrase)
            if p_match and p_status in ["EXACT_MATCH", "ALIAS_MATCH", "NORMALIZED_MATCH", "STRONG_MATCH"]:
                if p_match["id"] not in matched_by_id:
                    matched_by_id[p_match["id"]] = p_match
                    consumed_indices.update(span_indices)

    return list(matched_by_id.values())


def resolve_prospect_context(
    user_message: str,
    active_prospect: Optional[str] = None,
    active_prospect_id: Optional[str] = None
) -> ProspectContextResolutionResult:
    """
    GENERIC PROSPECT CONTEXT RESOLVER.
    Evaluates every user message against the active prospect context and multi-prospect comparative queries.
    """
    raw_msg = (user_message or "").strip()
    clean_active = (active_prospect or "").strip()

    # 1. Resolve canonical active prospect (if present)
    canonical_active_name = None
    canonical_active_id = active_prospect_id

    if clean_active and clean_active.lower() not in ["general", "unknown", "none", ""]:
        act_match, _, _ = resolve_prospect(clean_active)
        if act_match:
            canonical_active_name = act_match["name"]
            canonical_active_id = canonical_active_id or act_match.get("id")
        else:
            canonical_active_name = clean_active

    # 2. Check Greetings and Non-Business inquiries
    if is_general_chat_greeting(raw_msg):
        return ProspectContextResolutionResult(
            intent="general_chat",
            prospect_reference="no_prospect",
            active_prospect=canonical_active_name,
            active_prospect_id=canonical_active_id,
            reason="User input is a general conversation greeting."
        )

    if is_unsupported_request(raw_msg):
        return ProspectContextResolutionResult(
            intent="unsupported",
            prospect_reference="no_prospect",
            active_prospect=canonical_active_name,
            active_prospect_id=canonical_active_id,
            reason="User input is an unsupported external request."
        )

    # 3. Detect requested parameter (e.g. "Financial Strength", "Company Scale")
    detected_param = detect_parameter_match(raw_msg)

    # 4. Check for Comparative Intent & Extract Multiple Prospects
    is_comparative_phrase = bool(re.search(r'\b(?:compare|comparison|versus|vs|who has higher|who is larger|who is growing faster|better solvency|between)\b', raw_msg, re.IGNORECASE))
    all_mentioned_prospects = _extract_all_mentioned_prospects(raw_msg)

    # Comparative Case: User explicitly used comparative phrasing (e.g. "compare X and Y", "X vs Y")
    if is_comparative_phrase:
        comp_names = [p["name"] for p in all_mentioned_prospects]
        if canonical_active_name and canonical_active_name not in comp_names:
            comp_names.insert(0, canonical_active_name)

        if len(comp_names) >= 2:
            return ProspectContextResolutionResult(
                intent="prospect_comparison",
                prospect_reference="comparative",
                comparison_prospects=comp_names[:3],
                active_prospect=canonical_active_name,
                active_prospect_id=canonical_active_id,
                requested_parameter=detected_param,
                requires_switch_confirmation=False,
                confidence=0.98,
                reason=f"User requested multi-prospect comparison between: {', '.join(comp_names[:3])}."
            )
        elif not all_mentioned_prospects:
            return ProspectContextResolutionResult(
                intent="prospect_analysis",
                prospect_reference="ambiguous",
                active_prospect=canonical_active_name,
                active_prospect_id=canonical_active_id,
                requested_parameter=detected_param,
                reason="Comparative query requires specifying which second prospect to compare with."
            )

    # 5. Extract Single Mentioned Company
    mentioned_record = None
    if all_mentioned_prospects:
        mentioned_record = all_mentioned_prospects[0]

    # Fallback to Ollama if no match found
    if not mentioned_record:
        ollama_data = _extract_company_with_ollama(raw_msg, canonical_active_name)
        if ollama_data and isinstance(ollama_data, dict):
            candidate_name = ollama_data.get("mentioned_prospect")
            if candidate_name and isinstance(candidate_name, str) and candidate_name.strip():
                m_rec, m_cands, m_status = resolve_prospect(candidate_name.strip())
                if m_rec:
                    mentioned_record = m_rec
                elif m_status == "MULTIPLE_MATCHES" and m_cands:
                    return ProspectContextResolutionResult(
                        intent="prospect_analysis",
                        mentioned_prospect=candidate_name.strip(),
                        prospect_reference="ambiguous",
                        active_prospect=canonical_active_name,
                        active_prospect_id=canonical_active_id,
                        requested_parameter=detected_param,
                        candidates=m_cands,
                        reason="Multiple matching prospects found matching the requested query."
                    )
            if not detected_param and ollama_data.get("requested_parameter"):
                detected_param = detect_parameter_match(str(ollama_data.get("requested_parameter"))) or str(ollama_data.get("requested_parameter"))

    # 6. Apply Decision Rules: Compare Mentioned Prospect with Active Prospect
    if mentioned_record:
        canonical_mentioned_name = mentioned_record["name"]
        canonical_mentioned_id = mentioned_record.get("id")

        if canonical_active_name:
            is_same = (
                canonical_mentioned_name.lower() == canonical_active_name.lower() or
                (canonical_active_id and canonical_mentioned_id and canonical_active_id == canonical_mentioned_id)
            )

            if is_same:
                # CASE A: User explicitly mentioned the active prospect
                return ProspectContextResolutionResult(
                    intent="prospect_analysis",
                    mentioned_prospect=canonical_mentioned_name,
                    mentioned_prospect_id=canonical_mentioned_id,
                    prospect_reference="active_prospect",
                    active_prospect=canonical_active_name,
                    active_prospect_id=canonical_active_id,
                    requested_parameter=detected_param,
                    requires_switch_confirmation=False,
                    confidence=0.98,
                    reason=f"User explicitly referenced the active prospect '{canonical_active_name}'."
                )
            else:
                # CASE B: User explicitly mentioned a DIFFERENT prospect -> STOP & TRIGGER SWITCH
                return ProspectContextResolutionResult(
                    intent="prospect_analysis",
                    mentioned_prospect=canonical_mentioned_name,
                    mentioned_prospect_id=canonical_mentioned_id,
                    prospect_reference="different_prospect",
                    active_prospect=canonical_active_name,
                    active_prospect_id=canonical_active_id,
                    requested_parameter=detected_param,
                    requires_switch_confirmation=True,
                    confidence=0.98,
                    reason=f"User explicitly mentioned '{canonical_mentioned_name}', which differs from active prospect '{canonical_active_name}'."
                )
        else:
            # No active prospect -> Target this mentioned prospect directly
            return ProspectContextResolutionResult(
                intent="prospect_analysis",
                mentioned_prospect=canonical_mentioned_name,
                mentioned_prospect_id=canonical_mentioned_id,
                prospect_reference="different_prospect",
                active_prospect=None,
                active_prospect_id=None,
                requested_parameter=detected_param,
                requires_switch_confirmation=False,
                confidence=1.0,
                reason=f"Target prospect '{canonical_mentioned_name}' resolved with no prior active prospect."
            )

    # 7. No explicit foreign prospect mentioned in user message
    if canonical_active_name:
        return ProspectContextResolutionResult(
            intent="prospect_analysis",
            mentioned_prospect=None,
            mentioned_prospect_id=None,
            prospect_reference="active_prospect",
            active_prospect=canonical_active_name,
            active_prospect_id=canonical_active_id,
            requested_parameter=detected_param,
            requires_switch_confirmation=False,
            confidence=0.95,
            reason=f"User query implicitly targets the currently active prospect '{canonical_active_name}'."
        )

    # No active prospect and no mentioned prospect
    return ProspectContextResolutionResult(
        intent="prospect_analysis",
        prospect_reference="no_prospect",
        active_prospect=None,
        active_prospect_id=None,
        requested_parameter=detected_param,
        requires_switch_confirmation=False,
        reason="No active or mentioned prospect identified in context."
    )
