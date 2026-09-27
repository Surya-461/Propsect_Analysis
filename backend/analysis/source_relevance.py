"""
Source Relevance & Claim Matching Module.
Filters harvested research sources against final Parameter Summaries and Key Facts,
ensuring that displayed sources under 'Grounded Evidence & Verified Sources' directly support
the factual statements in the summary while keeping output minimal (1 to 3 sources max).
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from models.evidence import Evidence
from analysis.summarizer import clean_fact_text, is_clean_informative_fact

logger = logging.getLogger(__name__)

# Corporate and NLP stopwords ignored when token scoring against claim text
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what", "which",
    "this", "that", "these", "those", "then", "just", "so", "than", "such", "both",
    "through", "about", "for", "is", "of", "to", "in", "with", "on", "at", "by",
    "from", "up", "about", "into", "over", "after", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "can",
    "could", "should", "would", "will", "may", "might", "must", "shall", "company",
    "insurance", "insurer", "insurers", "carrier", "carriers", "group", "limited",
    "ltd", "corp", "inc", "plc", "report", "reported", "indicates", "disclosures",
    "verified", "according", "data", "year", "quarter"
}

# Domains disqualified from being displayed as verified supporting sources
DISQUALIFIED_DOMAINS: Set[str] = {
    "wikipedia.org", "en.wikipedia.org", "google.com", "google.co.in",
    "bing.com", "yahoo.com", "search.yahoo.com", "baidu.com", "duckduckgo.com"
}


def extract_claims(summary: str, key_facts: List[str]) -> List[str]:
    """
    Extracts individual factual claim statements from summary text and key facts list.
    Protects abbreviations (e.g. 'No. 1', 'Inc.') from being split prematurely.
    """
    claims = []
    
    # Process summary sentences
    if summary and not summary.startswith("Insufficient"):
        cleaned_summary = clean_fact_text(summary)
        # Protect abbreviations like No. 1, No. 2, Inc., Ltd.
        protected = re.sub(r'\b(No|Mr|Mrs|Dr|Inc|Ltd|Co|Vol|vs)\.\s+(\d+|[A-Z])', r'\1__abbr__\2', cleaned_summary)
        sentences = re.split(r'(?<=[.!?])\s+', protected)
        for s in sentences:
            s_clean = s.replace('__abbr__', '. ').strip()
            if len(s_clean) >= 15 and not s_clean.startswith("Insufficient"):
                claims.append(s_clean)
                
    # Process key facts
    if key_facts:
        for kf in key_facts:
            kf_clean = clean_fact_text(str(kf)).strip()
            if len(kf_clean) >= 12 and not kf_clean.startswith("Insufficient"):
                if kf_clean not in claims:
                    claims.append(kf_clean)
                    
    return claims


def extract_claim_features(claim: str) -> Dict[str, Any]:
    """
    Extracts key figures, metrics, rankings, and distinctive tokens from a claim sentence.
    """
    claim_lower = claim.lower()
    normalized_claim = re.sub(r'no\.\s*', 'no ', claim_lower)
    
    figures = set()
    fig_pattern = re.compile(r'\b(?:no\s*\d+|\d+(?:\.\d+)?%?|\d+[\d,.]*\s*(?:crore|lakh|billion|trillion|million|x)?)\b', re.IGNORECASE)
    for match in fig_pattern.finditer(normalized_claim):
        figures.add(match.group(0).strip())
        
    for match in re.finditer(r'\b\d+\b', claim_lower):
        figures.add(match.group(0).strip())
        
    words = re.findall(r'[a-zA-Z0-9]+', claim_lower)
    meaningful_tokens = set(w for w in words if w not in STOPWORDS and len(w) >= 3 and not w.isdigit())
    
    return {
        "text": claim,
        "figures": figures,
        "tokens": meaningful_tokens
    }


# ==============================================================================
# PROPOSAL ANALYSIS MULTI-SOURCE SYNTHESIS & RELEVANCE TOOLS
# ==============================================================================

def classify_source_relevance(
    company_name: str,
    parameter_name: str,
    evidence: Evidence,
    param_keywords: Optional[List[str]] = None
) -> str:
    """
    Classifies a candidate evidence source as:
      - 'RELEVANT': Contains substantive facts/metrics/capabilities directly matching the parameter.
      - 'PARTIALLY_RELEVANT': Mentions high-level business or company activities related to the domain.
      - 'IRRELEVANT': No meaningful parameter match, noise, or unrelated marketing/careers text.
      - 'DUPLICATE': Duplicate content matching already seen text.
    """
    raw_text = (evidence.content if evidence.content and len(evidence.content) > len(evidence.title or "") else (evidence.title or "")).lower()
    clean_text = clean_fact_text(raw_text)

    if not clean_text or len(clean_text) < 20 or not is_clean_informative_fact(clean_text):
        return "IRRELEVANT"

    # Disqualified search noise / portals
    url_str = (evidence.source_url or "").lower()
    if any(dq in url_str for dq in DISQUALIFIED_DOMAINS):
        return "IRRELEVANT"

    # Strict company token presence verification: reject generic industry articles that don't mention the company
    comp_clean = re.sub(r'[^a-z0-9\s]', ' ', (company_name or '').lower())
    comp_tokens = [t for t in comp_clean.split() if t not in STOPWORDS and len(t) >= 3]
    if comp_tokens and not any(ct in clean_text for ct in comp_tokens):
        return "IRRELEVANT"

    # Check parameter-specific keywords
    p_name_lower = parameter_name.lower()
    p_tokens = [t for t in re.findall(r'[a-zA-Z0-9]+', p_name_lower) if t not in STOPWORDS and len(t) >= 3]

    keywords = set(param_keywords or [])
    for t in p_tokens:
        keywords.add(t)

    # General parameter domain synonyms
    if "claim" in p_name_lower:
        keywords.update(["claim", "settlement", "adjudication", "fnol", "turnaround", "loss ratio", "tpa", "payout", "fraud"])
    elif "underwriting" in p_name_lower:
        keywords.update(["underwriting", "pricing", "combined ratio", "risk intake", "solvency", "appetite", "loss ratio", "retention"])
    elif "ai" in p_name_lower or "ml" in p_name_lower:
        keywords.update(["ai", "artificial intelligence", "machine learning", "ml", "automation", "algorithm", "model", "predictive", "cognitive"])
    elif "digital" in p_name_lower or "tech" in p_name_lower:
        keywords.update(["portal", "cloud", "api", "platform", "digital", "system", "integration", "software", "infrastructure"])
    elif "regulatory" in p_name_lower or "compliance" in p_name_lower:
        keywords.update(["license", "regulatory", "compliance", "solvency", "irdai", "naic", "statutory", "audit", "rating", "capital"])

    matched_kw_count = sum(1 for kw in keywords if kw in clean_text)

    # Check for substantive figures/metrics
    has_metrics = bool(re.search(r'\b\d+(?:\.\d+)?%|\b\d+[\d,.]*\s*(?:crore|lakh|billion|million|ratio|x)\b', clean_text))

    if matched_kw_count >= 2 or (matched_kw_count >= 1 and has_metrics):
        return "RELEVANT"
    elif matched_kw_count == 1 or has_metrics:
        return "PARTIALLY_RELEVANT"
    else:
        return "IRRELEVANT"


def build_tagged_evidence_context(
    company_name: str,
    parameter_name: str,
    raw_evidence_list: List[Evidence],
    param_keywords: Optional[List[str]] = None,
    max_snippet_len: int = 750
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Evaluates candidate research evidence, classifies relevance, eliminates duplicates/noise,
    and builds an explicitly tagged prompt context block with up to `max_snippet_len` characters per source.

    Returns:
      - tagged_prompt_text: Formatted string [Source 1], [Source 2], etc.
      - prepared_sources: List of clean structured source items for API/UI.
      - audit_metadata: Debug metadata with relevance classifications.
    """
    valid_ev = [e for e in (raw_evidence_list or []) if getattr(e, "content", None) or getattr(e, "title", None)]
    seen_texts = set()
    seen_urls = set()

    classified_items = []
    prepared_sources = []
    tagged_blocks = []

    for ev in valid_ev:
        raw_passage = ev.content if ev.content and len(ev.content) > len(ev.title or "") else (ev.title or "")
        cleaned_passage = clean_fact_text(raw_passage)

        # Truncate to maximum snippet length preserving natural sentence boundaries
        if len(cleaned_passage) > max_snippet_len:
            boundary = cleaned_passage[:max_snippet_len].rfind('.')
            if boundary > 300:
                cleaned_passage = cleaned_passage[:boundary + 1]
            else:
                cleaned_passage = cleaned_passage[:max_snippet_len].rstrip('.') + "..."

        text_fingerprint = cleaned_passage.lower()[:80]
        url_str = ev.source_url or ""

        if text_fingerprint in seen_texts:
            rel_class = "DUPLICATE"
        else:
            rel_class = classify_source_relevance(company_name, parameter_name, ev, param_keywords)

        if rel_class in ("RELEVANT", "PARTIALLY_RELEVANT") and text_fingerprint not in seen_texts:
            seen_texts.add(text_fingerprint)
            if url_str:
                seen_urls.add(url_str)

            source_index = len(prepared_sources) + 1
            src_name = ev.source_name or f"{company_name} Official Disclosure"

            source_dict = {
                "source_id": f"Source {source_index}",
                "source": src_name,
                "url": url_str,
                "summary": cleaned_passage,
                "relevance": rel_class
            }
            if getattr(ev, "published_date", None):
                source_dict["published_date"] = str(ev.published_date).strip()
            prepared_sources.append(source_dict)

            # Build tagged prompt block
            date_line = f"Date: {ev.published_date}\n" if getattr(ev, "published_date", None) else ""
            tagged_blocks.append(
                f"[Source {source_index} | {src_name}]\n"
                f"URL: {url_str or 'Not provided'}\n"
                f"{date_line}"
                f"Relevance: {rel_class}\n"
                f"Passage: {cleaned_passage}"
            )

        classified_items.append({
            "source_name": ev.source_name or "Unknown Source",
            "url": url_str,
            "classification": rel_class,
            "snippet_preview": cleaned_passage[:100]
        })

    tagged_prompt_text = "\n\n".join(tagged_blocks) if tagged_blocks else "No verified public evidence available."

    audit_metadata = {
        "parameter": parameter_name,
        "total_retrieved": len(valid_ev),
        "relevant_count": sum(1 for c in classified_items if c["classification"] == "RELEVANT"),
        "partially_relevant_count": sum(1 for c in classified_items if c["classification"] == "PARTIALLY_RELEVANT"),
        "ignored_count": sum(1 for c in classified_items if c["classification"] in ("IRRELEVANT", "DUPLICATE")),
        "classifications": classified_items
    }

    return tagged_prompt_text, prepared_sources, audit_metadata


def filter_and_align_sources(
    finding: str,
    reasoning: str,
    gaps: List[str],
    prepared_sources: List[Dict[str, Any]],
    company_name: str
) -> List[Dict[str, Any]]:
    """
    Validates bidirectional alignment between the generated summary finding and the prepared sources.
    Only sources that genuinely contributed to or support the factual finding are returned for display.
    """
    if not prepared_sources or not finding or finding.startswith("No authoritative public disclosures") or finding.startswith("Insufficient"):
        return []

    claims = extract_claims(f"{finding} {reasoning}", gaps)
    claim_features = [extract_claim_features(c) for c in claims if c]

    aligned_sources = []
    seen_urls = set()

    for src in prepared_sources:
        url_str = src.get("url", "")
        if url_str and url_str in seen_urls:
            continue

        raw_snippet = src.get("summary", "")
        cleaned_snippet = clean_fact_text(raw_snippet).lower()

        # Score evidence overlap against claims
        matches_claim = False
        for cf in claim_features:
            claim_figs = cf["figures"]
            claim_tokens = cf["tokens"]

            # Figure match
            if claim_figs and any(fig in cleaned_snippet for fig in claim_figs):
                matches_claim = True
                break

            # Token overlap match
            token_matches = sum(1 for tok in claim_tokens if tok in cleaned_snippet)
            if token_matches >= 2:
                matches_claim = True
                break

        # If source is relevant and contributed to overall domain context
        if matches_claim or src.get("relevance") == "RELEVANT":
            if url_str:
                seen_urls.add(url_str)
            aligned_sources.append({
                "source": src.get("source") or f"{company_name} Disclosure",
                "url": url_str,
                "summary": src.get("summary", "")
            })

    # If all prepared sources were relevant, retain up to 4
    if not aligned_sources and prepared_sources:
        for src in prepared_sources[:4]:
            aligned_sources.append({
                "source": src.get("source") or f"{company_name} Disclosure",
                "url": src.get("url", ""),
                "summary": src.get("summary", "")
            })

    return aligned_sources[:4]

