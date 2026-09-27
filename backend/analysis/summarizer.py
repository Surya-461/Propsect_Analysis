import re
import logging
from typing import Dict, Any, List, Optional

from ai.ollama import (
    summarize_analysis_with_ollama,
    PRIMARY_OLLAMA_MODEL,
    FALLBACK_OLLAMA_MODEL
)
from ai.gemini import summarize_analysis_with_gemini
from models.evidence import Evidence

logger = logging.getLogger(__name__)

SENTENCE_INDICATORS = {
    'is', 'are', 'was', 'were', 'has', 'have', 'had', 'recorded', 'reported', 
    'grew', 'increased', 'decreased', 'reached', 'stood', 'generated', 'operates', 
    'provides', 'holds', 'manages', 'expanded', 'achieved', 'includes', 'rating', 
    'assets', 'revenue', 'profit', 'premium', 'ratio', 'growth', 'workforce', 
    'employees', 'offices', 'branches', 'network', 'market', 'share', 'scale', 
    'valuation', 'billion', 'trillion', 'crore', 'lakh', 'million', 'capital', 'solvency',
    'total', 'equity', 'liabilities', 'underwriting', 'business', 'company', 'financial'
}

RAW_NOISE_STARTS = (
    'select year', 'select month', 'select date', 'form no', 'form a-', 'form 10-', 'form 8-', 'form 20-', 
    'schedules forming', 'disclosure under regulation', 'fund revenue account', 'break-up of cash', 
    'registration no', 'particulars', 'outside india', 'total (ul', 'break-up of', 'note:', 'sr. no', 
    'page ', 'table ', 'schedules forming part', 'click here', 'read more', 'privacy policy', 'cookie policy'
)

def is_clean_informative_fact(text: str) -> bool:
    """Evaluates whether a snippet contains informative natural language rather than raw table dumps or form noise."""
    if not text or len(text) < 10:
        return False
    t_lower = text.lower().strip()
    if any(t_lower.startswith(noise) for noise in RAW_NOISE_STARTS):
        return False
    if "verified empirical disclosures" in t_lower or "audited statutory filing and empirical" in t_lower:
        return False
    # Discard pure currency selector text
    if re.search(r'\$\s*usd\b.*?(?:eur|inr|gbp|cad|aud)', t_lower):
        return False
    # Discard pure TOC page chains
    if re.search(r'(\b\d+-\d+\b\s*){2,}', t_lower):
        return False
    digits = sum(1 for c in text if c.isdigit())
    letters = sum(1 for c in text if c.isalpha())
    if letters < 3:
        return False
    if (digits / (letters + 1)) > 0.85:
        return False
    return True

def clean_fact_text(text: str) -> str:
    """Cleans up snippet text, removing HTML, tables, raw PDF numbers, markdown artifacts, and statutory navigation noise."""
    if not text:
        return ""
    text = text.replace('₹', 'INR ')
    text = re.sub(r'!\[.*?\]\(.*?\)', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\(.*?\)', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\|[^\n]+\|', ' ', text)
    text = re.sub(r'\|', ' ', text)
    text = re.sub(r'(?:-\s*){3,}', ' ', text)
    text = re.sub(r'(?:_\s*){3,}', ' ', text)
    text = re.sub(r'(?:\.\s*){4,}', ' ', text)
    # Strip currency selector strings (e.g. $ USD €EURINR INR£GBP$CAD$AUD$NZD$HKD$SGD)
    text = re.sub(r'\$\s*USD\b.*?(?:EUR|INR|GBP|CAD|AUD|SGD)', ' ', text, flags=re.IGNORECASE)
    # Strip navigation headers
    text = re.sub(r'Companies:\s*\d+[\d,]*\s*total market cap:.*?(?:Sign In|Propose a change)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'Sign In\s+ENEnglish.*?(?:Propose a change|Your message)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'Propose a change\s+Your message has been sent.*', ' ', text, flags=re.IGNORECASE)
    # Strip hyphenated PDF TOC page number chains (e.g. 94-247 248-460 461-470 02-93)
    text = re.sub(r'(\b\d+-\d+\b\s*){2,}', ' ', text)
    text = re.sub(r'Schedules Forming Part.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Form A-[A-Z]+.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'FORM\s+[A-Z0-9\-]+.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Fund Revenue Account.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Break-up of cash.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Registration No\..*?(?:IRDAI|March|\d{4})', '', text, flags=re.IGNORECASE)
    text = re.sub(r'See accompanying notes.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Disclosure under Regulation.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(\b\d+[\d,.]*\b\s*){4,}', ' ', text)
    text = re.sub(r'Select Year:.*?No records found', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Select Year:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'No records found', '', text, flags=re.IGNORECASE)
    # Strip web crawl sidebar noise, related story lists, and RSS artifacts
    text = re.sub(r'\[\s*\.\.\.\s*\]|\(\s*\.\.\.\s*\)|\.{3,}', ' ', text)
    text = re.sub(
        r'(?:Source:\s*)?(?:Latest|Related|Trending|Recent|Popular|Top|Must\s+Read|Also\s+Read|Read\s+More|More\s+From|Editor\'s\s+Pick|Recommended)\s+(?:Stories|News|Articles|Posts|Topics|Updates|Headlines)?\s*:\s*.*?(?=(?:\.|\n|[A-Z][a-z]+|\bThe\b|\b[A-Z]{2,}\b|\bIn\b|\bAt\b|\bOn\b|\bWith\b|\bUnder\b|$))',
        ' ',
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r'(?:Also\s+Read|Must\s+Read|Read\s+More|Related\s+Article|Related\s+Post|Recommended\s+Reading)\s*:.*?(?=(?:\.|\n|$|[A-Z][a-z]+|\bThe\b))',
        ' ',
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r'\b(?:Source|Via):\s*(?:Latest\s+Stories|Reuters|Bloomberg|PTI|IANS|TechCrunch|ET\s+Now)\b.*?(?=[A-Z][a-z]+|\bThe\b|$)',
        ' ',
        text,
        flags=re.IGNORECASE
    )
    # Strip common crawled news aggregate headlines
    text = re.sub(r'Decagon\s+Achieves.*?Research\s+Warns', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    cleaned = ' '.join(text.split())
    return cleaned

def limit_to_sentences(text: str, max_sentences: int = 8) -> str:
    """Enforces a clean summary of up to max_sentences sentences."""
    if not text or not text.strip():
        return ""

    cleaned = clean_fact_text(text)
    raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    valid = []
    for s in raw_sentences:
        s_clean = s.strip()
        if is_clean_informative_fact(s_clean):
            valid.append(s_clean)

    if not valid:
        if len(cleaned) >= 15 and not any(cleaned.lower().startswith(n) for n in RAW_NOISE_STARTS):
            valid = [cleaned[:600]]
        else:
            return ""

    result = " ".join(valid[:max_sentences])
    if len(result) > 1400:
        cutoff = result[:1300].rfind('.')
        if cutoff > 300:
            result = result[:cutoff + 1]
        else:
            result = result[:1300].rstrip('.') + "."
            
    if result and not result.endswith(('.', '!', '?')):
        result += "."
    return result


def find_parameter_data(parsed_params: dict, target_key: str) -> dict:
    """Finds parameter dict using exact or fuzzy key matching."""
    if not isinstance(parsed_params, dict):
        return {}
    if target_key in parsed_params and isinstance(parsed_params[target_key], dict):
        return parsed_params[target_key]
    
    target_clean = re.sub(r'[^a-z0-9]', '', target_key.lower())
    for k, v in parsed_params.items():
        if isinstance(v, dict):
            k_clean = re.sub(r'[^a-z0-9]', '', k.lower())
            if target_clean in k_clean or k_clean in target_clean or (len(target_clean) > 4 and target_clean[:4] in k_clean):
                return v
    return {}


def summarize_all_parameters(
    company_name: str,
    evidence_by_param: Dict[str, List[Evidence]],
    preferred_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesizes research intelligence across all parameters.
    Fallback flow: Primary provider (Gemini) -> Secondary provider (Ollama).
    If both fail, logs both error details and raises RuntimeError.
    Each parameter is analyzed in strict isolation.
    Top 5 valid results cap per parameter.
    Missing evidence yields 'Insufficient Data — Not Found in Public Sources'.
    """
    total_valid_evidence = sum(len(ev_list) for ev_list in evidence_by_param.values())
    total_evidence_text_len = sum(
        sum(len(e.content or "") for e in ev_list if e.content)
        for ev_list in evidence_by_param.values()
    )

    if total_valid_evidence == 0 or total_evidence_text_len < 20:
        raise ValueError(f"No public research evidence or disclosures found for '{company_name}'.")

    def build_sources_for_param(evidence_list: List[Evidence]) -> List[Dict[str, str]]:
        sources = []
        valid_ev = [
            e for e in (evidence_list or [])
            if getattr(e, "source_url", None) and str(e.source_url).startswith("http")
        ]
        seen_urls = set()
        for ev in valid_ev:
            url_str = ev.source_url or ""
            if not url_str or not url_str.startswith("http"):
                continue
            if any(sd in url_str.lower() for sd in ["google.com/search", "google.co.in/search", "bing.com/search", "search.yahoo.com"]):
                continue
            if url_str in seen_urls:
                continue
            seen_urls.add(url_str)

            raw_ev = ev.content if ev.content and len(ev.content) > len(ev.title) else ev.title
            clean_ev = clean_fact_text(raw_ev)
            if not is_clean_informative_fact(clean_ev):
                clean_ev = clean_fact_text(ev.title or "")
            if not is_clean_informative_fact(clean_ev):
                clean_ev = f"Verified public disclosure for {company_name}"
            source_entry = {
                "name": ev.source_name or f"{company_name} Disclosure",
                "url": url_str,
                "evidence": clean_ev[:200] if clean_ev else ""
            }
            if getattr(ev, "published_date", None):
                source_entry["published_date"] = str(ev.published_date).strip()
            sources.append(source_entry)
            if len(sources) >= 3:
                break
        return sources[:3]

    from ai.llm_provider import get_configured_llm_provider
    provider = (preferred_provider or get_configured_llm_provider()).strip().lower()

    logger.info("[AI] Starting parameter analysis for: %s (Configured Provider: %s)", company_name, provider)

    ai_result = None
    ai_error = None
    gemini_err = None
    ollama_err = None

    if provider in ("gemini", "google"):
        logger.info("[AI] Executing Gemini primary for parameter summary generation for '%s'", company_name)
        try:
            res = summarize_analysis_with_gemini(company_name, evidence_by_param)
            if isinstance(res, dict) and "parameters" in res and res.get("parameters"):
                ai_result = res
        except Exception as exc:
            gemini_err = str(exc)
            logger.warning("[AI] Gemini summary generation failed for '%s': %s. Falling back to Ollama (%s)...", company_name, exc, PRIMARY_OLLAMA_MODEL)

        # Fallback to Ollama if Gemini failed
        if not ai_result:
            models_to_try = [PRIMARY_OLLAMA_MODEL]
            if FALLBACK_OLLAMA_MODEL and FALLBACK_OLLAMA_MODEL != PRIMARY_OLLAMA_MODEL:
                models_to_try.append(FALLBACK_OLLAMA_MODEL)
            for m_name in models_to_try:
                try:
                    logger.info("[AI] Executing Ollama fallback (%s) for '%s'", m_name, company_name)
                    res = summarize_analysis_with_ollama(company_name, evidence_by_param, model_name=m_name)
                    if isinstance(res, dict) and "parameters" in res and res.get("parameters"):
                        ai_result = res
                        logger.info("[AI] Ollama (%s) fallback successfully generated parameter summary for '%s'", m_name, company_name)
                        break
                except Exception as exc:
                    ollama_err = str(exc)
                    logger.error("[AI] Ollama (%s) fallback summary generation failed for '%s': %s", m_name, company_name, exc)
    else:
        logger.info("[AI] Executing Ollama primary (%s) for parameter summary generation for '%s'", PRIMARY_OLLAMA_MODEL, company_name)
        try:
            res = summarize_analysis_with_ollama(company_name, evidence_by_param, model_name=PRIMARY_OLLAMA_MODEL)
            if isinstance(res, dict) and "parameters" in res and res.get("parameters"):
                ai_result = res
        except Exception as exc:
            ollama_err = str(exc)
            logger.warning("[AI] Ollama summary generation failed for '%s': %s. Falling back to Gemini...", company_name, exc)

        # Fallback to Gemini if Ollama failed
        if not ai_result:
            try:
                logger.info("[AI] Executing Gemini fallback for '%s'", company_name)
                res = summarize_analysis_with_gemini(company_name, evidence_by_param)
                if isinstance(res, dict) and "parameters" in res and res.get("parameters"):
                    ai_result = res
                    logger.info("[AI] Gemini fallback successfully generated parameter summary for '%s'", company_name)
            except Exception as exc:
                gemini_err = str(exc)
                logger.error("[AI] Gemini fallback summary generation failed for '%s': %s", company_name, exc)

    if not ai_result or not isinstance(ai_result, dict) or "parameters" not in ai_result or not ai_result.get("parameters"):
        causes = []
        if gemini_err:
            causes.append(f"Gemini error: {gemini_err}")
        if ollama_err:
            causes.append(f"Ollama error: {ollama_err}")
        cause_str = " | ".join(causes) if causes else "AI models returned empty or invalid structured JSON."
        error_msg = (
            f"AI summarization service is currently unavailable for '{company_name}'. "
            f"{cause_str}"
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    # Process and format isolated parameters
    parsed_params = ai_result.get("parameters", {}) if isinstance(ai_result, dict) else {}
    exec_summary = (ai_result.get("executive_summary") if isinstance(ai_result, dict) else "") or ""
    top_param_summaries = []

    final_params = {}

    for param_key, ev_list in evidence_by_param.items():
        p_val = find_parameter_data(parsed_params, param_key)
        valid_ev = [e for e in (ev_list or []) if getattr(e, "source_url", None) or getattr(e, "content", None)]

        if not valid_ev:
            final_params[param_key] = {
                "summary": "Insufficient Data — Not Found in Public Sources",
                "finding_classification": "Insufficient Evidence",
                "key_facts": ["Insufficient Data — Not Found in Public Sources"],
                "sources": []
            }
            continue

        raw_summary = (
            p_val.get("summary")
            or p_val.get("description")
            or p_val.get("analysis")
            or p_val.get("insight")
            or p_val.get("findings_summary")
            or p_val.get("overview")
            or p_val.get("explanation")
            or ""
        )
        raw_summary_str = str(raw_summary).strip()
        clean_sum = limit_to_sentences(raw_summary_str, max_sentences=8)
        if not clean_sum and len(raw_summary_str) >= 15:
            clean_sum = clean_fact_text(raw_summary_str)

        raw_facts = (
            p_val.get("key_facts")
            or p_val.get("evidence")
            or p_val.get("findings")
            or p_val.get("insights")
            or p_val.get("observations")
            or p_val.get("facts")
            or p_val.get("disclosures")
            or []
        )
        if isinstance(raw_facts, str):
            raw_facts = [raw_facts]
        clean_facts = []
        seen_facts = set()
        for f in raw_facts:
            c = clean_fact_text(str(f))
            if is_clean_informative_fact(c) and c.lower()[:40] not in seen_facts:
                seen_facts.add(c.lower()[:40])
                clean_facts.append(c[:220])
                if len(clean_facts) >= 5:
                    break

        if not clean_sum:
            if valid_ev:
                candidate_sentences = []
                for ev in valid_ev:
                    content_text = ev.content or ev.title or ""
                    clean_ev_text = clean_fact_text(content_text)
                    if is_clean_informative_fact(clean_ev_text):
                        for s in re.split(r'(?<=[.!?])\s+', clean_ev_text):
                            s_strip = s.strip()
                            if is_clean_informative_fact(s_strip) and len(s_strip) >= 20:
                                if not any(s_strip.lower()[:30] == c.lower()[:30] for c in candidate_sentences):
                                    candidate_sentences.append(s_strip)
                if candidate_sentences:
                    clean_sum = limit_to_sentences(" ".join(candidate_sentences[:4]), max_sentences=4)
                    clean_facts = candidate_sentences[:5]

            if not clean_sum:
                if ai_error:
                    clean_sum = "Summary could not be generated. Please try again."
                else:
                    clean_sum = "Insufficient Data — Not Found in Public Sources"

        if not clean_facts:
            if clean_sum.startswith("Insufficient"):
                clean_facts = ["Insufficient Data — Not Found in Public Sources"]
            elif clean_sum.startswith("Summary could not"):
                clean_facts = ["Summary could not be generated. Please try again."]
            else:
                clean_facts = [clean_sum[:220]]

        finding_class = (
            p_val.get("finding_classification")
            or p_val.get("classification")
        )
        if not finding_class or finding_class not in ["Strong Fit", "Partial Fit", "Gap", "Insufficient Evidence"]:
            if "insufficient" in clean_sum.lower() or "not found" in clean_sum.lower():
                finding_class = "Insufficient Evidence"
            elif "gap" in clean_sum.lower() or "exposure" in clean_sum.lower():
                finding_class = "Partial Fit"
            else:
                finding_class = "Strong Fit"

        final_params[param_key] = {
            "summary": clean_sum,
            "finding_classification": finding_class,
            "key_facts": clean_facts[:5],
            "sources": build_sources_for_param(valid_ev)[:5]
        }

        if clean_sum and not clean_sum.startswith("Insufficient") and not clean_sum.startswith("Summary could not"):
            top_param_summaries.append(clean_sum)

    if not exec_summary or len(exec_summary.strip()) < 20:
        if top_param_summaries:
            exec_summary = limit_to_sentences(" ".join(top_param_summaries[:3]), max_sentences=6)
        else:
            exec_summary = f"Commercial underwriting intelligence analysis for {company_name} compiled across core research parameters."

    # Process underwriting verdict
    raw_verdict = ai_result.get("underwriting_verdict") if isinstance(ai_result, dict) else {}
    if not isinstance(raw_verdict, dict):
        raw_verdict = {}

    overall_risk = str(raw_verdict.get("overall_risk_level") or raw_verdict.get("risk_level") or "Medium").capitalize()
    if overall_risk not in ("Low", "Medium", "High"):
        overall_risk = "Medium"

    exposure_classes = raw_verdict.get("primary_exposure_classes") or []
    if isinstance(exposure_classes, str):
        exposure_classes = [exposure_classes]
    clean_exposures = [str(x).strip() for x in exposure_classes if str(x).strip()]
    if not clean_exposures:
        clean_exposures = ["Property / BI", "General Liability", "Workers Compensation"]

    entry_trigger = str(raw_verdict.get("entry_point_trigger") or "No immediate entry point identified").strip()

    underwriting_verdict = {
        "overall_risk_level": overall_risk,
        "primary_exposure_classes": clean_exposures[:5],
        "entry_point_trigger": entry_trigger
    }

    # Process critical data gaps
    raw_gaps = ai_result.get("critical_data_gaps") if isinstance(ai_result, dict) else []
    if isinstance(raw_gaps, str):
        raw_gaps = [raw_gaps]
    clean_gaps = [str(g).strip() for g in (raw_gaps or []) if str(g).strip()]

    if not clean_gaps:
        for p_name, p_data in final_params.items():
            if p_data.get("finding_classification") == "Insufficient Evidence" or p_data.get("summary", "").startswith("Insufficient"):
                clean_gaps.append(f"Statutory loss runs and detailed disclosures for {p_name} not available in public registries.")

    # Extract metrics_scorecard if populated by AI
    metrics_scorecard = ai_result.get("metrics_scorecard") if isinstance(ai_result, dict) else None
    if not isinstance(metrics_scorecard, dict):
        metrics_scorecard = {}

    return {
        "parameters": final_params,
        "executive_summary": limit_to_sentences(exec_summary, max_sentences=8),
        "underwriting_verdict": underwriting_verdict,
        "critical_data_gaps": clean_gaps[:5],
        "metrics_scorecard": metrics_scorecard,
        "risk_rating": overall_risk
    }

