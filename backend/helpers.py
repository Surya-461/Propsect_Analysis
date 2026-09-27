import re
import datetime
import logging
from analysis.summarizer import clean_fact_text, limit_to_sentences, is_clean_informative_fact
from services.intent_service import detect_parameter_match as intent_detect_parameter_match

logger = logging.getLogger(__name__)

def detect_parameter_match(question: str, explicit_param: str | None = None) -> str | None:
    """Detects matching target parameter name dynamically via intent_service."""
    return intent_detect_parameter_match(question, explicit_param)

def extract_parameter_content(param_name: str, param_value: dict, company_name: str = "") -> dict:
    """
    Extracts actual content from the existing parameter result supporting all backend
    and LLM output schemas without changing the architecture.
    Never generates generic placeholder fallbacks when research evidence exists.
    """
    if not isinstance(param_value, dict):
        param_value = {}

    # 1. Summary candidates
    raw_summary = (
        param_value.get("summary")
        or param_value.get("description")
        or param_value.get("analysis")
        or param_value.get("insight")
        or param_value.get("insights_summary")
        or param_value.get("findings_summary")
        or param_value.get("explanation")
        or param_value.get("overview")
        or (param_value.get("findings") if isinstance(param_value.get("findings"), str) else "")
        or (param_value.get("research") if isinstance(param_value.get("research"), str) else "")
        or (param_value.get("content") if isinstance(param_value.get("content"), str) else "")
        or ""
    )
    clean_sum = limit_to_sentences(str(raw_summary), max_sentences=8)

    # 2. Key Facts candidates
    raw_key_facts = (
        param_value.get("key_facts")
        or param_value.get("evidence")
        or param_value.get("findings")
        or param_value.get("insights")
        or param_value.get("observations")
        or param_value.get("facts")
        or param_value.get("disclosures")
        or param_value.get("highlights")
        or param_value.get("points")
        or param_value.get("research")
        or []
    )
    if isinstance(raw_key_facts, str):
        raw_key_facts = [raw_key_facts]
    if not isinstance(raw_key_facts, list):
        raw_key_facts = [str(raw_key_facts)] if raw_key_facts else []

    cleaned_facts = []
    seen_fact_keys = set()
    for fact in raw_key_facts:
        f_str = clean_fact_text(str(fact))
        if is_clean_informative_fact(f_str):
            norm_k = f_str.lower()[:40]
            if norm_k not in seen_fact_keys:
                seen_fact_keys.add(norm_k)
                cleaned_facts.append(f_str[:220])

    # 3. Sources candidates
    raw_sources = (
        param_value.get("sources")
        or param_value.get("citations")
        or param_value.get("references")
        or param_value.get("links")
        or []
    )
    if isinstance(raw_sources, str):
        raw_sources = [raw_sources]
    if not isinstance(raw_sources, list):
        raw_sources = [str(raw_sources)] if raw_sources else []

    cleaned_sources = []
    seen_source_urls = set()
    for item in raw_sources:
        if isinstance(item, dict):
            name = item.get("name") or item.get("title") or item.get("source") or f"{company_name} Disclosure"
            url = item.get("url") or item.get("link") or ""
            ev = clean_fact_text(item.get("evidence") or item.get("content") or item.get("snippet") or "")
            pub_date = item.get("published_date") or item.get("date") or item.get("published") or None
            if not is_clean_informative_fact(ev):
                ev = clean_fact_text(str(name))
            if url and url.startswith("http") and not any(sd in url.lower() for sd in ["google.com/search", "google.co.in/search", "bing.com/search", "search.yahoo.com"]):
                if url not in seen_source_urls:
                    seen_source_urls.add(url)
                    source_entry = {"name": str(name), "url": str(url), "evidence": ev[:200]}
                    if pub_date:
                        source_entry["published_date"] = str(pub_date).strip()
                    cleaned_sources.append(source_entry)
        else:
            s_str = str(item).strip()
            if s_str.startswith("http") and not any(sd in s_str.lower() for sd in ["google.com/search", "google.co.in/search", "bing.com/search", "search.yahoo.com"]):
                if s_str not in seen_source_urls:
                    seen_source_urls.add(s_str)
                    cleaned_sources.append({"name": f"{company_name} Verified Citation", "url": s_str, "evidence": ""})

        if len(cleaned_sources) >= 5:
            break

    if not clean_sum and cleaned_facts:
        clean_sum = limit_to_sentences(" ".join(cleaned_facts[:3]), max_sentences=4)

    if not clean_sum:
        clean_sum = "Insufficient Data — Not Found in Public Sources"
    if not cleaned_facts:
        if clean_sum.startswith("Insufficient"):
            cleaned_facts = ["Insufficient Data — Not Found in Public Sources"]
        elif clean_sum.startswith("Summary could not"):
            cleaned_facts = ["Summary could not be generated. Please try again."]
        else:
            cleaned_facts = [clean_sum[:220]]

    finding_classification = (
        param_value.get("finding_classification")
        or param_value.get("classification")
        or ("Insufficient Evidence" if "insufficient" in clean_sum.lower() else "Strong Fit")
    )

    return {
        "finding_classification": finding_classification,
        "summary": clean_sum,
        "explanation": clean_sum,
        "key_facts": cleaned_facts[:5],
        "sources": cleaned_sources[:5]
    }

def normalize_analysis_payload(report_dict: dict) -> dict:
    """Normalizes and cleans raw research analysis output payload for UI consistency."""
    normalized = {}
    if not isinstance(report_dict, dict):
        return normalized

    for param_name, param_value in report_dict.items():
        if not isinstance(param_name, str) or not isinstance(param_value, dict):
            continue

        extracted = extract_parameter_content(param_name, param_value)

        metrics = param_value.get("metrics") or []
        cleaned_metrics = []
        for m in metrics:
            if isinstance(m, dict):
                cleaned_metrics.append({
                    "prospect": str(m.get("prospect", "")),
                    "parameter": param_name,
                    "metric": str(m.get("metric", "Metric")),
                    "segment": str(m.get("segment", "General")),
                    "sub_segment": str(m.get("sub_segment", "General")),
                    "period": str(m.get("period", "FY2024-25")),
                    "value": str(m.get("value", "Not available")),
                    "formatted_value": str(m.get("formatted_value", m.get("value", "Not available"))),
                    "unit": str(m.get("unit", "actual")),
                    "currency": str(m.get("currency", "INR")),
                    "table_title": str(m.get("table_title", f"{param_name} Disclosures")),
                    "source": str(m.get("source", "Public Disclosure")),
                    "source_page": m.get("source_page"),
                    "source_url": str(m.get("source_url", "")),
                    "confidence": str(m.get("confidence", "Medium")),
                    "is_total": bool(m.get("is_total", False)),
                    "reconciliation_status": str(m.get("reconciliation_status", "Reconciled")),
                    "metric_identity": str(m.get("metric_identity", ""))
                })

        discrepancies = param_value.get("discrepancies") or []
        checklist = param_value.get("checklist") or []
        cleaned_checklist = [
            {
                "parameter": str(item.get("parameter", param_name)),
                "label": str(item.get("label", "Checklist item")),
                "status": str(item.get("status", "review")),
                "value": str(item.get("value", "Requires underwriter review"))
            }
            for item in checklist
            if isinstance(item, dict)
        ]

        normalized[param_name] = {
            "parameter": param_name,
            "finding_classification": extracted.get("finding_classification", "Strong Fit"),
            "score": param_value.get("score", 80),
            "confidence": param_value.get("confidence", "High"),
            "status": param_value.get("status", "Analyzed"),
            "metrics_used": param_value.get("metrics_used", len(cleaned_metrics)),
            "evidence_count": param_value.get("evidence_count", len(extracted["sources"])),
            "last_updated": param_value.get("last_updated", datetime.date.today().isoformat()),
            "metrics": cleaned_metrics,
            "explanation": extracted["summary"],
            "summary": extracted["summary"],
            "key_facts": extracted["key_facts"][:5],
            "checklist": cleaned_checklist,
            "discrepancies": discrepancies,
            "sources": extracted["sources"][:5]
        }

    return normalized


def validate_prospect_input(name: str, domain: str = "Insurance") -> tuple[bool, str]:
    """
    Dynamic Input Validator for Insurance Domains & Prospect Analysis.
    Delegates to central validation service powered by Ollama.
    """
    from services.validation_service import validate_prospect_input as v_func
    return v_func(name, domain=domain)

def validate_domain_input(domain_name: str, input_payload: dict) -> tuple[bool, str, dict]:
    """
    Dynamically validates incoming requests against registered insurance domain schemas.
    Delegates to central validation service.
    """
    from services.validation_service import validate_domain_input as v_func
    return v_func(domain_name, input_payload)


def verify_prospect_evidence(company_name: str, evidence_by_param: dict[str, list]) -> tuple[bool, str]:
    """
    Evaluates research evidence harvested for company_name to verify prospect legitimacy.
    """
    total_count = sum(len([e for e in ev_list if e.source_url or e.content]) for ev_list in evidence_by_param.values())
    if total_count == 0:
        return False, "No research sources found."

    total_content_length = sum(
        sum(len(e.content or "") for e in ev_list if e.content)
        for ev_list in evidence_by_param.values()
    )
    if total_content_length < 100:
        return False, "Insufficient empirical research content length."

    from research.source_manager import GENERIC_STOPWORDS, SEARCH_NOISE_PHRASES
    raw_tokens = re.findall(r'[a-zA-Z]+', company_name.lower())
    significant_tokens = [t for t in raw_tokens if len(t) >= 3 and t not in GENERIC_STOPWORDS]
    if not significant_tokens:
        significant_tokens = [t for t in raw_tokens if len(t) >= 3]

    if significant_tokens:
        has_title_match = False
        for ev_list in evidence_by_param.values():
            for ev in ev_list:
                t_lower = (ev.title or "").lower()
                c_head = (ev.content[:150] if ev.content else "").lower()
                searchable = f"{t_lower} {c_head}"
                if any(phrase in searchable for phrase in SEARCH_NOISE_PHRASES):
                    continue
                if any(tok in searchable for tok in significant_tokens):
                    has_title_match = True
                    break
            if has_title_match:
                break

        if not has_title_match:
            return False, "No reliable evidence item matched company title."

    return True, "Prospect verified with reliable empirical evidence."
