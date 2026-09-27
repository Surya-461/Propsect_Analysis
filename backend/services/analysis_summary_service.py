"""
Analysis Summary Service for Proposal-Based Prospect Analysis.
Generates clean, professional plain-text executive synthesis containing:
- Overall Assessment
- Strongest Alignment
- Key Gaps
- Opportunity Signals
- Risks / Unknowns
- Recommended Contact Angle
- Recommended Next Action

Enforces strict plain-text formatting with zero Markdown syntax (#, **, *, _, `, bullets, links, separators).
"""

import re
from typing import Dict, Any, List, Optional
import logging

from ai.gemini import query_gemini
from ai.ollama import query_ollama, PRIMARY_OLLAMA_MODEL

logger = logging.getLogger(__name__)


def remove_score_language(text: str) -> str:
    """
    Strips all numerical scores, score terminology, and score presentations
    (e.g., '(85/100)', '61/100', 'score of 61/100', 'High Fit score', 'Fit score', 'Score: 85').
    """
    if not text:
        return ""
    t = str(text)
    # Remove bracketed/parenthesized scores, e.g. (85/100), (61/100), (Score: 85), (85%), [85/100]
    t = re.sub(r'[\(\[]\s*(?:Score:\s*)?\d+(?:\.\d+)?\s*/\s*100\s*[\)\]]', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[\(\[]\s*\d+(?:\.\d+)?%\s*[\)\]]', '', t)
    t = re.sub(r'[\(\[]\s*Score:\s*\d+\s*[\)\]]', '', t, flags=re.IGNORECASE)
    # Remove standalone /100 score patterns like "score of 61/100", "61/100", "85/100"
    t = re.sub(r'\b(?:an?\s+)?(?:overall\s+)?(?:high|moderate|medium|low|very high)?\s*fit\s+score\s+(?:of\s+)?\d+(?:\.\d+)?(?:\s*/\s*100)?\b', 'strong overall alignment', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(?:an?\s+)?(?:overall\s+)?score\s+(?:of\s+)?\d+(?:\.\d+)?(?:\s*/\s*100)?\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\b\d+(?:\.\d+)?\s*/\s*100\b', '', t)
    # Remove phrases like "High Fit score of", "Fit score of", "Fit Score:"
    t = re.sub(r'\b(?:High|Moderate|Low|Very High)\s+Fit\s+score\b', 'alignment', t, flags=re.IGNORECASE)
    t = re.sub(r'\bFit\s+score\b', 'alignment', t, flags=re.IGNORECASE)
    t = re.sub(r'\bConfidence\s+Score:\s*\d+\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\bFit\s+Score:\s*\d+\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\bOverall\s+Score:\s*\d+\b', '', t, flags=re.IGNORECASE)
    # Clean up double colons or orphaned colons like "Parameter: : "
    t = re.sub(r':\s*:', ':', t)
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip()


def clean_plain_text(text: str) -> str:
    """
    Strips all Markdown formatting syntax (headings, bold, italics, bullets, backticks, links, code blocks)
    and any numerical score language while preserving the underlying words and plain-text sentence structure.
    """
    if not text:
        return ""
    t = str(text)
    # Remove score language first
    t = remove_score_language(t)
    # Remove code blocks
    t = re.sub(r'```[a-zA-Z0-9_-]*\n(.*?)```', r'\1', t, flags=re.DOTALL)
    t = re.sub(r'`([^`]+)`', r'\1', t)
    # Remove Markdown headings (#, ##, ###, etc.)
    t = re.sub(r'^\s*#{1,6}\s*', '', t, flags=re.MULTILINE)
    # Remove bold/italic markers (**text**, *text*, __text__, _text_)
    t = re.sub(r'\*\*([^*]+)\*\*', r'\1', t)
    t = re.sub(r'\*([^*]+)\*', r'\1', t)
    t = re.sub(r'__([^_]+)__', r'\1', t)
    t = re.sub(r'_([^_]+)_', r'\1', t)
    # Remove Markdown links [text](url) -> text
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    # Remove horizontal rules
    t = re.sub(r'^\s*[-*_]{3,}\s*$', '', t, flags=re.MULTILINE)
    # Remove bullet prefixes (- , * , + , • ) at line starts
    t = re.sub(r'^\s*[-*+•]\s+', '', t, flags=re.MULTILINE)
    # Remove numbered list prefixes (1. , 2. ) at line starts
    t = re.sub(r'^\s*\d+\.\s+', '', t, flags=re.MULTILINE)
    # Clean up double/multiple blank lines and whitespace
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


def generate_proposal_executive_summary(
    prospect_name: str,
    proposal_profile: Dict[str, Any],
    parameter_results: List[Dict[str, Any]],
    overall_score: Optional[int] = None,
    fit_level: Optional[str] = None,
    mock_mode: bool = False
) -> Dict[str, Any]:
    """
    Synthesizes the mandatory final analysis summary for Proposal-Based Prospect Analysis.
    Uses LLM synthesis grounded strictly on the evaluated parameters and evidence,
    returning clean plain text without Markdown syntax or score-based language.
    """
    proposal_title = proposal_profile.get("proposal_title", "Uploaded Proposal")
    domain = proposal_profile.get("domain", "Commercial Insurance")
    
    # Extract top aligned parameters from results
    top_alignments = [p["parameter"] for p in parameter_results if p.get("finding")]
    if not top_alignments:
        top_alignments = ["Commercial Operations", "Domain Relevance"]

    # Extract all observed gaps
    all_gaps: List[str] = []
    for p in parameter_results:
        gaps = p.get("gaps") or []
        for g in gaps:
            clean_g = clean_plain_text(str(g))
            if clean_g and clean_g not in all_gaps:
                all_gaps.append(clean_g)

    # Deterministic fallback synthesis (used when mock_mode=True or AI models are offline)
    fallback_assessment = clean_plain_text(
        f"{prospect_name} demonstrates notable proposal alignment across {', '.join(top_alignments[:3])} "
        f"for the {proposal_title} requirements. "
        f"While business and operational capabilities appear aligned, active procurement scope and budget "
        f"remain to be validated through direct underwriting engagement."
    )

    fallback_contact = clean_plain_text(
        f"Position the conversation around operational efficiency, automated decision support, "
        f"and seamless integration with {prospect_name}'s existing commercial insurance operations."
    )

    fallback_action = clean_plain_text(
        f"Identify the relevant underwriting transformation, enterprise architecture, or innovation "
        f"stakeholder at {prospect_name} to validate whether there is an active or upcoming modernization initiative."
    )

    if mock_mode:
        final_assessment = fallback_assessment
        final_strongest = [
            clean_plain_text(f"{p['parameter']}: {p.get('finding', '')[:120]}")
            for p in parameter_results[:3] if p.get("parameter")
        ]
        if not final_strongest:
            final_strongest = [clean_plain_text(str(item)) for item in (top_alignments[:4] or ["Commercial Operations", "Domain Relevance"])]
        
        final_gaps = [clean_plain_text(str(g)) for g in (all_gaps[:3] or ["Current procurement status and budget allocation are not publicly confirmed."])]
        final_signals = [
            f"Active digital transformation initiatives and modernization disclosures observed for {prospect_name}.",
            "Commercial insurance portfolio expansion indicating demand for operational efficiency."
        ]
        final_risks = [
            "Unknown: Public sources do not confirm an active commercial RFP budget for this fiscal period.",
            "Operational Risk: Integration complexity with internal legacy underwriting and core systems."
        ]
        final_contact = fallback_contact
        final_next_action = fallback_action

        strongest_text = ". ".join([s.rstrip('.') for s in final_strongest if s])
        if strongest_text and not strongest_text.endswith('.'):
            strongest_text += "."

        gaps_text = ". ".join([g.rstrip('.') for g in final_gaps if g])
        if gaps_text and not gaps_text.endswith('.'):
            gaps_text += "."

        signals_text = ". ".join([s.rstrip('.') for s in final_signals if s])
        if signals_text and not signals_text.endswith('.'):
            signals_text += "."

        risks_text = ". ".join([r.rstrip('.') for r in final_risks if r])
        if risks_text and not risks_text.endswith('.'):
            risks_text += "."

        consolidated_text = (
            f"Executive Analysis Summary\n\n"
            f"Overall Assessment\n"
            f"{final_assessment}\n\n"
            f"Strongest Alignment Areas\n"
            f"{strongest_text}\n\n"
            f"Key Gaps and Missing Evidence\n"
            f"{gaps_text}\n\n"
            f"Opportunity Signals\n"
            f"{signals_text}\n\n"
            f"Risks and Unknowns\n"
            f"{risks_text}\n\n"
            f"Recommended Contact Angle\n"
            f"{final_contact}\n\n"
            f"Recommended Next Action\n"
            f"{final_next_action}"
        )

        return {
            "overall_assessment": final_assessment,
            "strongest_alignment": final_strongest,
            "key_gaps": final_gaps,
            "opportunity_signals": final_signals,
            "risks_and_unknowns": final_risks,
            "recommended_contact_angle": final_contact,
            "recommended_next_action": final_next_action,
            "summary": consolidated_text
        }

    # Collect concise findings for prompt context
    findings_context = "\n".join([
        f"- {p['parameter']} (Category: {p.get('category', 'General')}, Fit Level: {p.get('fit_level', 'High')}, Confidence: {p.get('confidence', 'Medium')}): {clean_plain_text(p.get('finding', ''))}"
        for p in parameter_results
    ])

    prompt = f"""You are an executive commercial insurance strategist.
Generate an authoritative, professional Proposal Fit Executive Summary evaluating:

Prospect: {prospect_name}
Proposal/RFP: {proposal_title} (Domain: {domain})

PARAMETER EVALUATION FINDINGS & EVIDENCE SUMMARY:
{findings_context}

CRITICAL DIRECTIVES:
1. NO NUMERICAL SCORES OR SCORE LANGUAGE:
   - Do NOT provide numerical scores, percentages, scores out of 100, weighted scores, or any numerical fit scoring.
   - Do NOT include score values in the Overall Assessment, Strongest Alignment Areas, Key Gaps, Parameter Analysis, or any other user-facing analysis section.
   - The model should return qualitative analysis based on evidence.
   - Allowed terminology: High, Medium, Low, Strong alignment, Moderate alignment, Limited alignment, Weak alignment, High confidence, Medium confidence, Low confidence.
   - Strictly prohibited: 61/100, 85/100, 75/100, 85%, Fit Score: 85, Overall Score: 61, High Fit Score, Confidence Score: 90, "score of", "score".
2. OVERALL ASSESSMENT FORMAT:
   - 2 to 4 sentence evidence-based qualitative assessment explaining:
     * Overall business/proposal alignment
     * Strongest supporting evidence
     * Important limitations or mismatches
     * Relevant risks or missing evidence
   - Do NOT include numerical scores, percentages, "score", "score of X/100", "High Fit score", or confidence score.
3. STRONGEST ALIGNMENT AREAS:
   - Name each top matching area followed by the evidence/finding as qualitative text WITHOUT numerical scores or (XX/100) suffixes.
   - Format: "Parameter Name: High adherence / operational capability description..."
   - Example: "Regulatory and Compliance Fit: High adherence to IRDAI governance, statutory reporting, solvency margins, and data privacy mandates."
4. PLAIN TEXT ONLY:
   - Return the final Executive Analysis Summary and Overall Assessment as plain text only. Never use Markdown formatting or Markdown syntax (#, ##, ###, **text**, *text*, _text_, backticks, Markdown bullets, tables, separators, or links).
5. STRICT FACTUAL GROUNDING:
   - Base all findings strictly on the evaluated parameters above. Do NOT invent capabilities or speculate.

Return a strict JSON object with this exact schema:
{{
  "overall_assessment": "Comprehensive 2-4 sentence qualitative evidence-based assessment of how well the prospect fits this specific proposal as clean plain text without any numerical scores.",
  "strongest_alignment": [
    "Parameter Name: High-level descriptive alignment summary without score",
    "Parameter Name: High-level descriptive alignment summary without score"
  ],
  "key_gaps": [
    "Primary gap or missing confirmation 1",
    "Primary gap or missing confirmation 2"
  ],
  "opportunity_signals": [
    "Public signal indicating technology modernization or strategic appetite",
    "Market or commercial growth indicator supporting alignment"
  ],
  "risks_and_unknowns": [
    "Unknown: Public information does not confirm active procurement budget or RFP timeline",
    "Risk: Integration dependencies with existing core legacy systems"
  ],
  "recommended_contact_angle": "How an enterprise producer or solution architect should position the initial outreach in plain text.",
  "recommended_next_action": "Specific practical next step in plain text."
}}
"""

    ai_summary = None
    gemini_err = None
    ollama_err = None
    try:
        ai_resp = query_gemini(prompt, json_output=True, timeout=40)
        if isinstance(ai_resp, dict) and "overall_assessment" in ai_resp and "recommended_contact_angle" in ai_resp:
            ai_summary = ai_resp
    except Exception as e:
        gemini_err = str(e)
        logger.warning("[AnalysisSummaryService] Gemini summary generation issue: %s", e)

    if not ai_summary:
        try:
            ollama_resp = query_ollama(prompt, json_output=True, timeout=35, model_name=PRIMARY_OLLAMA_MODEL)
            if isinstance(ollama_resp, dict) and "overall_assessment" in ollama_resp:
                ai_summary = ollama_resp
        except Exception as e:
            ollama_err = str(e)
            logger.warning("[AnalysisSummaryService] Ollama summary generation issue: %s", e)

    if not ai_summary and not mock_mode:
        causes = []
        if gemini_err:
            causes.append(f"Gemini error: {gemini_err}")
        if ollama_err:
            causes.append(f"Ollama error: {ollama_err}")
        cause_str = " | ".join(causes) if causes else "AI models returned empty or invalid summary payload."
        error_msg = (
            f"AI Summary Generation failed for '{prospect_name}': Both Gemini and Ollama were unavailable or failed to produce summary. "
            f"Tier 3 fallback has been removed. ({cause_str})"
        )
        logger.error("[AnalysisSummaryService] %s", error_msg)
        raise RuntimeError(error_msg)

    # Sanitize all outputs to ensure zero Markdown syntax exists
    raw_assessment = (ai_summary.get("overall_assessment") if ai_summary else None) or fallback_assessment
    final_assessment = clean_plain_text(raw_assessment)

    raw_strongest = (ai_summary.get("strongest_alignment") if ai_summary and ai_summary.get("strongest_alignment") else None) or top_alignments or ["Commercial Operations", "Domain Relevance"]
    final_strongest = [clean_plain_text(str(x)) for x in raw_strongest if clean_plain_text(str(x))]

    raw_gaps = (ai_summary.get("key_gaps") if ai_summary and ai_summary.get("key_gaps") else None) or all_gaps[:3] or ["Current procurement status and budget allocation are not publicly confirmed."]
    final_gaps = [clean_plain_text(str(x)) for x in raw_gaps if clean_plain_text(str(x))]

    raw_signals = (ai_summary.get("opportunity_signals") if ai_summary and ai_summary.get("opportunity_signals") else None) or [
        f"Active digital transformation initiatives and modernization disclosures observed for {prospect_name}.",
        "Commercial insurance portfolio expansion indicating demand for operational efficiency."
    ]
    final_signals = [clean_plain_text(str(x)) for x in raw_signals if clean_plain_text(str(x))]

    raw_risks = (ai_summary.get("risks_and_unknowns") if ai_summary and ai_summary.get("risks_and_unknowns") else None) or [
        "Unknown: Public sources do not confirm an active commercial RFP budget for this fiscal period.",
        "Operational Risk: Integration complexity with internal legacy underwriting and core systems."
    ]
    final_risks = [clean_plain_text(str(x)) for x in raw_risks if clean_plain_text(str(x))]

    raw_contact = (ai_summary.get("recommended_contact_angle") if ai_summary else None) or fallback_contact
    final_contact = clean_plain_text(raw_contact)

    raw_action = (ai_summary.get("recommended_next_action") if ai_summary else None) or fallback_action
    final_next_action = clean_plain_text(raw_action)

    strongest_text = ". ".join([s.rstrip('.') for s in final_strongest if s])
    if strongest_text and not strongest_text.endswith('.'):
        strongest_text += "."

    gaps_text = ". ".join([g.rstrip('.') for g in final_gaps if g])
    if gaps_text and not gaps_text.endswith('.'):
        gaps_text += "."

    signals_text = ". ".join([s.rstrip('.') for s in final_signals if s])
    if signals_text and not signals_text.endswith('.'):
        signals_text += "."

    risks_text = ". ".join([r.rstrip('.') for r in final_risks if r])
    if risks_text and not risks_text.endswith('.'):
        risks_text += "."

    consolidated_text = (
        f"Executive Analysis Summary\n\n"
        f"Overall Assessment\n"
        f"{final_assessment}\n\n"
        f"Strongest Alignment Areas\n"
        f"{strongest_text}\n\n"
        f"Key Gaps and Missing Evidence\n"
        f"{gaps_text}\n\n"
        f"Opportunity Signals\n"
        f"{signals_text}\n\n"
        f"Risks and Unknowns\n"
        f"{risks_text}\n\n"
        f"Recommended Contact Angle\n"
        f"{final_contact}\n\n"
        f"Recommended Next Action\n"
        f"{final_next_action}"
    )

    return {
        "overall_assessment": final_assessment,
        "strongest_alignment": final_strongest,
        "key_gaps": final_gaps,
        "opportunity_signals": final_signals,
        "risks_and_unknowns": final_risks,
        "recommended_contact_angle": final_contact,
        "recommended_next_action": final_next_action,
        "summary": consolidated_text
    }

