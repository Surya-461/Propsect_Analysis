import re
from typing import Any
from models.evidence import Evidence
from research.search_router import route_and_execute_research
from research.authority_ranker import score_evidence_item

MIN_SOURCES_PER_PARAMETER = 3
MAX_QUERIES_PER_PARAMETER = 2  # Hard cap: 2 queries * 8 parameters = 16 queries max per prospect

GENERIC_STOPWORDS = {
    "company", "insurance", "inc", "ltd", "llc", "corp", "corporation",
    "co", "group", "holdings", "limited", "the", "and", "of", "for", "in",
    "general", "life", "health"
}

SEARCH_NOISE_PHRASES = [
    "search results for", "no results found", "did you mean", "showing results for",
    "zero results", "nothing found", "no matching documents", "does not exist",
    "search query", "unknown query", "propose a change your message has been sent",
    "sign in enenglish", "sign in english deutsch"
]


FINANCIAL_INSURANCE_CONTEXT_TERMS = [
    "solvency", "solvency ratio", "solvency margin", "premium", "revenue", "profit",
    "assets", "total assets", "aum", "assets under management", "capital", "equity",
    "liabilities", "claims", "claim ratio", "loss ratio", "combined ratio", "underwriting",
    "employees", "workforce", "headcount", "crore", "inr", "percentage", "%", "₹",
    "financial results", "annual report", "pat", "ebitda", "net worth", "growth",
    "persistency", "gdpi", "gwp", "rating", "crisil", "icra", "irdai", "car", "ratio"
]


def is_relevant_evidence(company_name: str, ev: Evidence) -> bool:
    """
    Verifies that the evidence title or primary disclosure text actually mentions
    at least one significant alphabetic token of company_name.
    Rejects search engine query echoes, zero-result page snippets, currency tickers,
    hyphenated PDF TOC page lists, and irrelevant numeric noise without financial context.
    Preserves numeric tables when financial or insurance context exists.
    """
    if not company_name:
        return False

    title_text = (ev.title or "").lower()
    content_head = (ev.content[:300] if ev.content else "").lower()
    searchable_header = f"{title_text} {content_head}"

    # Discard search engine query echoes or zero-result page titles
    if any(phrase in searchable_header for phrase in SEARCH_NOISE_PHRASES):
        return False

    # Discard currency selector / ticker streams (e.g. $ USD EUR INR GBP CAD AUD)
    if re.search(r'\$\s*usd\b.*?(?:eur|inr|gbp|cad|aud)', content_head):
        return False

    # Context detection for financial / insurance numeric evidence
    has_financial_context = any(term in searchable_header for term in FINANCIAL_INSURANCE_CONTEXT_TERMS)

    # Discard page navigation lists (e.g., "Page 1 2 3 4 5 6 7 8 9" or "page 1 of 10 2 3 4")
    if re.search(r'\bpage\s*(?:\d+\s*){3,}', content_head) or re.search(r'^(?:\s*\d+\s+){5,}', content_head):
        if not has_financial_context:
            return False

    # Discard hyphenated PDF page-range chains (e.g. 94-247 248-460 461-470)
    if re.search(r'(\b\d+-\d+\b\s*){2,}', content_head):
        return False

    # Numeric-heavy content filtering:
    # If content has 4+ consecutive numeric tokens, preserve IF financial/insurance context exists.
    # Discard ONLY when it is raw numeric noise without domain context.
    if re.search(r'(\b\d+[\d,.]*\b\s*){4,}', content_head):
        if not has_financial_context:
            return False

    # Discard statutory accounting schedule dumps
    if any(header in searchable_header for header in [
        "schedules forming part", "form a-ra", "form a-bs",
        "break-up of cash", "fund revenue account for the year ended"
    ]):
        return False

    # 1. Discard or sanitize search engine result URLs
    url_lower = (ev.source_url or "").lower()
    if any(search_domain in url_lower for search_domain in ["google.com/search", "google.co.in/search", "bing.com/search", "search.yahoo.com"]):
        ev.source_url = ""

    c_name_lower = company_name.lower()

    # 2. Strict Sibling Entity Disambiguation Filtering
    # SBI Life vs SBI General vs State Bank of India
    if "sbi life" in c_name_lower:
        if ("sbi general" in searchable_header or "state bank of india" in searchable_header) and "sbi life" not in searchable_header:
            return False
    if "sbi general" in c_name_lower:
        if "sbi life" in searchable_header and "sbi general" not in searchable_header:
            return False

    # HDFC Life vs HDFC ERGO vs HDFC Bank
    if "hdfc life" in c_name_lower:
        if ("hdfc ergo" in searchable_header or "hdfc bank" in searchable_header) and "hdfc life" not in searchable_header:
            return False
    if "hdfc ergo" in c_name_lower:
        if ("hdfc life" in searchable_header or "hdfc bank" in searchable_header) and "hdfc ergo" not in searchable_header:
            return False

    # ICICI Prudential vs ICICI Lombard vs ICICI Bank
    if "icici pru" in c_name_lower or "prudential" in c_name_lower:
        if ("icici lombard" in searchable_header or "icici bank" in searchable_header) and "prudential" not in searchable_header:
            return False
    if "icici lombard" in c_name_lower or "lombard" in c_name_lower:
        if ("prudential" in searchable_header or "icici bank" in searchable_header) and "lombard" not in searchable_header:
            return False

    # Tata AIA vs Tata AIG vs Tata Sons
    if "tata aia" in c_name_lower:
        if ("tata aig" in searchable_header or "tata motors" in searchable_header or "tata consultancy" in searchable_header) and "aia" not in searchable_header:
            return False
    if "tata aig" in c_name_lower:
        if ("tata aia" in searchable_header or "tata motors" in searchable_header) and "aig" not in searchable_header:
            return False

    # Bajaj Allianz Life vs Bajaj Allianz General vs Bajaj Finance/Finserv
    if "bajaj allianz life" in c_name_lower:
        if ("bajaj allianz general" in searchable_header or "bajaj finance" in searchable_header or "bajaj auto" in searchable_header) and "life" not in searchable_header:
            return False
    if "bajaj allianz general" in c_name_lower or "bajaj allianz gic" in c_name_lower:
        if ("bajaj allianz life" in searchable_header or "bajaj finance" in searchable_header) and "general" not in searchable_header:
            return False

    # Kotak Mahindra Life vs Kotak Mahindra General vs Kotak Mahindra Bank
    if "kotak" in c_name_lower and "life" in c_name_lower:
        if ("kotak general" in searchable_header or "kotak mahindra bank" in searchable_header) and "life" not in searchable_header:
            return False
    if "kotak" in c_name_lower and "general" in c_name_lower:
        if ("kotak life" in searchable_header or "kotak mahindra bank" in searchable_header) and "general" not in searchable_header:
            return False

    # 3. Extract alphabetic tokens (excluding generic stopwords and numbers)
    raw_tokens = re.findall(r'[a-zA-Z]+', c_name_lower)
    significant_tokens = [t for t in raw_tokens if len(t) >= 3 and t not in GENERIC_STOPWORDS]

    if not significant_tokens:
        significant_tokens = [t for t in raw_tokens if len(t) >= 3]

    if not significant_tokens:
        return True

    # At least one significant token of company_name must appear in the title or primary header
    return any(token in searchable_header for token in significant_tokens)


PARAM_KEYWORDS = {
    "Financial Strength": ["financial", "solvency", "capital", "asset", "balance sheet", "profitability", "earnings", "revenue", "loss", "reserve"],
    "Insurance Performance": ["underwriting", "combined ratio", "claims", "gwp", "premium", "loss ratio", "actuarial", "persistency"],
    "Technology Activity": ["technology", "digital", "ai", "cloud", "it", "automation", "platform", "software", "fintech", "insurtech"],
    "Company Scale": ["scale", "revenue", "assets", "employees", "headcount", "workforce", "valuation", "enterprise"],
    "Business Growth": ["growth", "expansion", "year-over-year", "yoy", "momentum", "acquisition", "premium growth"],
    "Market Position": ["market share", "ranking", "position", "competitor", "leader", "peer", "brand"],
    "Operational Scale": ["branch", "distribution", "agent", "agency", "network", "office", "footprint", "bancassurance"],
    "Strategic Activity": ["strategic", "partnership", "m&a", "acquisition", "alliance", "joint venture", "launch"]
}

SOURCE_QUALITY_WEIGHTS = {
    "official": 1.0,
    "annual_report": 0.95,
    "regulatory_filing": 0.95,
    "investor_relations": 0.90,
    "reputable_news": 0.85,
    "wikipedia": 0.70,
    "general_web": 0.50
}


def calculate_evidence_score(company_name: str, parameter: str, ev: Evidence) -> float:
    """
    Computes multi-factor evidence score using authority_ranker.
    Preserved for backward-compatibility.
    """
    return score_evidence_item(company_name, parameter, ev)


def search_all_sources(
    company_name: str,
    parameter: str,
    search_queries: list[Any] | None = None,
    preferred_sources: list[str] | None = None,
    research_intents: list[Any] | None = None
) -> list[Evidence]:
    """
    Searches multiple independent public sources for a given parameter.
    Orchestrates Tavily, Serper.dev, Google News, Wikipedia, Financial RSS,
    Industry RSS, Annual Report linker, Firecrawl, deduplication, and conflict resolution.
    Supports both structured ResearchIntents and legacy search_queries.
    """
    evidence_items, _ = route_and_execute_research(
        company_name=company_name,
        parameter=parameter,
        search_queries=search_queries or [],
        preferred_sources=preferred_sources or [],
        max_queries=MAX_QUERIES_PER_PARAMETER,
        research_intents=research_intents
    )
    return evidence_items
