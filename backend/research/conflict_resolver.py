import re
from typing import Dict, List, Any, Optional, Tuple
from models.evidence import Evidence


# Reporting period regex patterns (e.g. FY2025, FY24, Q3 FY25, FY 2023-24, FY2024-25, 2024-25)
PERIOD_PATTERNS = [
    r'\b(?:FY|Q[1-4]\s*FY)?\s*(?:202[0-9]|201[0-9])(?:-(?:202[0-9]|2[0-9]))?\b',
    r'\bFY\s*2[0-9]\b',
    r'\bQ[1-4]\s*FY\s*2[0-9]\b'
]


def extract_reporting_period(text: str) -> Optional[str]:
    """
    Extracts explicit financial reporting period (e.g. FY2025, FY2024, Q3 FY25).
    """
    if not text:
        return None
    for pattern in PERIOD_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            clean_period = match.group(0).strip().upper()
            return clean_period
    return None


def extract_structured_metric_candidates(text: str, source_name: str, source_tier: int) -> List[Dict[str, Any]]:
    """
    Extracts key metric candidates with values, periods, units, and source attribution.
    """
    candidates = []
    if not text:
        return candidates

    period = extract_reporting_period(text) or "Current Period"

    # 1. Solvency Ratio pattern (e.g. solvency ratio 2.15x / 215% / 2.02)
    solvency_match = re.search(r'(?:solvency\s*ratio|solvency)\s*(?:of|is|stood at|was|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:x|\%|\b)', text, re.IGNORECASE)
    if solvency_match:
        val_str = solvency_match.group(1)
        candidates.append({
            "metric": "Solvency Ratio",
            "value": f"{val_str}x",
            "raw_number": float(val_str) if "." in val_str else float(val_str) / 100.0 if float(val_str) > 10 else float(val_str),
            "period": period,
            "source": source_name,
            "tier": source_tier
        })

    # 2. Revenue / GWP / AUM / Net Profit with currency
    curr_pattern = r'(?:revenue|total income|gross written premium|gwp|assets under management|aum|net profit|profit after tax|pat)\s*(?:of|is|was|stood at|reached|hit|:)?\s*(?:₹|INR|USD|\$)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(crore|cr|lakh|billion|million|trillion)?'
    for match in re.finditer(curr_pattern, text, re.IGNORECASE):
        metric_name = match.group(0).split()[0].title()
        val_str = match.group(1).replace(",", "")
        unit = (match.group(2) or "Crore").capitalize()
        try:
            raw_num = float(val_str)
            candidates.append({
                "metric": metric_name,
                "value": f"INR {raw_num:,.2f} {unit}",
                "raw_number": raw_num,
                "unit": unit,
                "period": period,
                "source": source_name,
                "tier": source_tier
            })
        except ValueError:
            pass

    return candidates


def resolve_metric_conflicts(
    metric_candidates: List[Dict[str, Any]]
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Hierarchical Conflict Resolution Engine.
    Rules:
    1. NEVER average conflicting values.
    2. Group candidates by (metric, period). Different periods are NOT conflicts.
    3. For identical (metric, period), prefer the candidate with highest authority (lowest tier number).
    4. If two Tier 1/2 sources disagree on same (metric, period), prioritize the highest authority and generate an explicit transparency notice.
    """
    resolved_by_metric: Dict[str, Dict[str, Any]] = {}
    conflict_notes: List[str] = []

    # Group by (metric, period)
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for c in metric_candidates:
        key = (c["metric"].lower(), c["period"].upper())
        grouped.setdefault(key, []).append(c)

    for (metric_key, period_key), cand_list in grouped.items():
        if not cand_list:
            continue

        # Sort by source authority tier ascending (1 is best), then raw_number descending
        cand_list.sort(key=lambda x: x.get("tier", 4))
        best_cand = cand_list[0]
        metric_name = best_cand["metric"]

        # Check for genuine same-period conflict
        distinct_values = set(c["value"] for c in cand_list)
        if len(distinct_values) > 1:
            tier1_or_2 = [c for c in cand_list if c.get("tier", 4) <= 2]
            if len(tier1_or_2) > 1:
                conflict_val_strs = ", ".join([f"{c['value']} ({c['source']})" for c in tier1_or_2[:2]])
                notice = (
                    f"The available sources report different figures for {metric_name} ({period_key}): {conflict_val_strs}. "
                    f"The official filing ({best_cand['source']}) reporting {best_cand['value']} has been prioritized."
                )
                conflict_notes.append(notice)

        resolved_by_metric[f"{metric_name}_{period_key}"] = best_cand

    return resolved_by_metric, conflict_notes


def curate_evidence_with_conflict_resolution(
    evidence_list: List[Evidence]
) -> Tuple[List[Evidence], List[str]]:
    """
    Curates evidence list, populates structured metrics, resolves conflicts without averaging,
    and returns (curated_evidence, conflict_disclosures).
    """
    all_metric_candidates: List[Dict[str, Any]] = []

    for ev in evidence_list:
        # Extract period if present
        period = extract_reporting_period(ev.content or "") or extract_reporting_period(ev.title or "")
        ev.reporting_period = period

        # Extract metric candidates
        candidates = extract_structured_metric_candidates(
            text=f"{ev.title} {ev.content}",
            source_name=ev.source_name,
            source_tier=ev.authority_tier
        )
        all_metric_candidates.extend(candidates)

    resolved_metrics, conflict_notes = resolve_metric_conflicts(all_metric_candidates)

    # Attach resolved metric disclosures to evidence metadata
    for ev in evidence_list:
        if ev.reporting_period:
            matching = [v for k, v in resolved_metrics.items() if ev.reporting_period.upper() in k]
            if matching:
                ev.metric_data = matching[0]

    return evidence_list, conflict_notes
