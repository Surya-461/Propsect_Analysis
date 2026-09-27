import re
from typing import List, Tuple
from models.evidence import Evidence
from research.normalizer import extract_domain

# Specific Domain Authority Mappings
TIER_1_DOMAINS = {
    # Insurance Regulators & Gov
    "irdai.gov.in", "naic.org", "bankofengland.co.uk", "fca.org.uk",
    "mca.gov.in", "incometaxindia.gov.in", "gov.in", "nic.in",
    "lifeinscouncil.org", "gi-council.org",
    # Official annual report / disclosures indicators
    "sbilife.co.in", "hdfclife.com", "iciciprulife.com", "maxlifeinsurance.com",
    "licindia.in", "bajajallianzlife.com", "tataaia.com", "allianz.com",
    "axa.com", "prudential.com", "metlife.com", "pingan.com", "zurich.com"
}

TIER_2_DOMAINS = {
    # Stock Exchanges
    "nseindia.com", "bseindia.com", "sec.gov", "londonstockexchange.com", "nyse.com",
    # Credit Rating Agencies
    "crisil.com", "icra.in", "careedge.in", "ambest.com", "moodys.com", "spglobal.com", "fitchratings.com",
    # Recognized Financial Databases
    "moneycontrol.com", "screener.in", "trendlyne.com", "tickertape.in", "capitalmarket.com"
}

TIER_3_DOMAINS = {
    # Major Global & National Business Publications
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "economictimes.indiatimes.com",
    "livemint.com", "business-standard.com", "cnbctv18.com", "thehindubusinessline.com",
    "forbes.com", "fortune.com", "marketwatch.com",
    # Established Insurance Industry Press
    "insurancejournal.com", "coverager.com", "insurancetimes.co.uk", "asiainsurancereview.com",
    "artemis.bm", "reinsurancene.ws"
}

TIER_5_DOMAINS = {
    "medium.com", "substack.com", "reddit.com", "quora.com", "blogspot.com",
    "wordpress.com", "linkedin.com/pulse", "tumblr.com", "wixsite.com"
}

TIER_SCORES = {
    1: 1.00,
    2: 0.88,
    3: 0.78,
    4: 0.60,
    5: 0.35
}

PARAM_PRIORITY_KEYWORDS = {
    "Financial Strength": {
        "tier1_keywords": ["solvency", "annual report", "audited", "balance sheet", "capital adequacy", "financial results", "investor presentation"],
        "preferred_types": ["annual_report", "regulatory_filing", "credit_rating_agency", "financial_report"],
        "authority_boost": 0.10
    },
    "Insurance Performance": {
        "tier1_keywords": ["combined ratio", "claims settlement", "gross written premium", "underwriting profit", "persistency ratio", "loss ratio"],
        "preferred_types": ["insurance_regulator", "annual_report", "underwriting_filings", "financial_report"],
        "authority_boost": 0.10
    },
    "Market Position": {
        "tier1_keywords": ["market share", "industry rank", "ranking", "peer comparison", "new business premium", "market leadership"],
        "preferred_types": ["industry_report", "regulatory_source", "annual_report", "reputable_news"],
        "authority_boost": 0.05
    },
    "Business Growth": {
        "tier1_keywords": ["premium growth", "quarterly results", "revenue expansion", "year-over-year", "yoy growth", "new customer"],
        "preferred_types": ["investor_relations", "annual_report", "financial_report", "reputable_news"],
        "authority_boost": 0.05
    },
    "Operational Scale": {
        "tier1_keywords": ["branch network", "bancassurance", "distribution footprint", "agent workforce", "offices", "customer touchpoints"],
        "preferred_types": ["company_website", "annual_report", "regulatory_source", "reputable_news"],
        "authority_boost": 0.05
    },
    "Technology Activity": {
        "tier1_keywords": ["digital transformation", "ai", "artificial intelligence", "cloud", "api", "automation", "core modernization"],
        "preferred_types": ["technology_news", "press_release", "company_website", "industry_case_study"],
        "authority_boost": 0.05
    },
    "Strategic Activity": {
        "tier1_keywords": ["merger", "acquisition", "m&a", "partnership", "joint venture", "bancassurance tie-up", "strategic alliance"],
        "preferred_types": ["press_release", "annual_report", "regulatory_filings", "reputable_news"],
        "authority_boost": 0.08
    },
    "Company Scale": {
        "tier1_keywords": ["total assets", "assets under management", "aum", "headcount", "workforce", "total revenue", "enterprise scale"],
        "preferred_types": ["annual_report", "regulatory_filing", "company_website", "reputable_news"],
        "authority_boost": 0.08
    }
}


def classify_source_authority(url: str, source_type: str = "", title: str = "", content: str = "") -> Tuple[int, float]:
    """
    Classifies a source into Priority Tiers 1-6 according to research source hierarchy:
    1. Prospect's official website, annual reports, regulatory filings (IRDAI, SEC, etc.) (Tier 1, Score 1.00/0.95)
    2. Stock exchanges & financial reports (Tier 2, Score 0.88)
    3. Prospect-specific credit ratings (Tier 3, Score 0.85)
    4. Reputable financial / news sources (Tier 4, Score 0.75)
    5. Other sources only when directly relevant (Tier 5, Score 0.50)
    """
    domain = extract_domain(url)
    combined_text = f"{title} {content} {url}".lower()

    # Priority 1: Prospect Official Website, Annual Reports & IRDAI/Gov Regulatory Filings
    if domain in TIER_1_DOMAINS or domain.endswith(".gov.in") or domain.endswith(".gov") or domain.endswith(".nic.in") or any(r in domain for r in ["irdai.gov.in", "mca.gov.in", "sec.gov", "lifeinscouncil.org"]):
        return 1, 1.00
    if source_type in ["company_website", "official_profile", "annual_report", "regulatory_filing"]:
        return 1, 0.95

    # Priority 2: Annual Reports / Financial Filings / Stock Exchanges
    if any(k in url.lower() for k in ["annual-report", "financial-results", "investor-relations", "filing"]) or source_type in ["financial_report"]:
        return 2, 0.90

    # Priority 3: Prospect-specific Credit Ratings
    if any(agency in combined_text or agency in domain for agency in ["crisil", "icra", "careedge", "ambest", "moodys", "spglobal"]):
        return 3, 0.85

    # Priority 4: Reputable Financial / News Sources
    if domain in TIER_3_DOMAINS or domain in TIER_2_DOMAINS or source_type in ["reputable_news", "industry_report"]:
        return 4, 0.75

    # Priority 5: Other sources
    return 5, 0.50


def score_evidence_item(company_name: str, parameter: str, ev: Evidence, distinct_domain_count: int = 1) -> float:
    """
    Computes rigorous multi-factor evidence score:
    evidence_score = (authority * 0.35) + (relevance * 0.25) + (recency * 0.15) + (directness * 0.15) + (cross_source * 0.10)
    """
    tier, auth_base = classify_source_authority(
        url=ev.source_url or "",
        source_type=ev.source_type or "",
        title=ev.title or "",
        content=ev.content or ""
    )
    ev.authority_tier = tier

    # Parameter-specific priority adjustment
    param_config = PARAM_PRIORITY_KEYWORDS.get(parameter, {})
    pref_types = param_config.get("preferred_types", [])
    tier1_kw = param_config.get("tier1_keywords", [])
    auth_boost = param_config.get("authority_boost", 0.0)

    auth_score = auth_base
    if ev.source_type in pref_types:
        auth_score = min(1.0, auth_score + auth_boost)

    combined_text = f"{ev.title or ''} {ev.content or ''}".lower()
    if any(kw in combined_text for kw in tier1_kw):
        auth_score = min(1.0, auth_score + 0.05)

    ev.authority_score = round(auth_score, 3)

    # 1. Relevance Score (Company match + Parameter Keyword match)
    from research.source_manager import GENERIC_STOPWORDS, PARAM_KEYWORDS
    c_tokens = [t for t in re.findall(r'[a-zA-Z]+', company_name.lower()) if len(t) >= 3 and t not in GENERIC_STOPWORDS]
    if not c_tokens:
        c_tokens = [t for t in re.findall(r'[a-zA-Z]+', company_name.lower()) if len(t) >= 3]

    c_match = 0.0
    if c_tokens:
        matches = sum(1 for tok in c_tokens if tok in combined_text)
        c_match = min(1.0, matches / len(c_tokens))

    param_keywords = PARAM_KEYWORDS.get(parameter, [])
    p_match = 0.0
    if param_keywords:
        p_hits = sum(1 for kw in param_keywords if kw in combined_text)
        p_match = min(1.0, p_hits / 2)

    relevance_score = round((0.60 * c_match) + (0.40 * p_match), 3)
    ev.relevance = relevance_score

    # 2. Recency Score
    recency_score = 0.85
    if ev.published_date:
        pub_lower = str(ev.published_date).lower()
        if any(yr in pub_lower for yr in ["2026", "2025", "2024", "fy25", "fy24"]):
            recency_score = 0.95
        elif any(yr in pub_lower for yr in ["2023", "fy23"]):
            recency_score = 0.80
        elif any(yr in pub_lower for yr in ["2022", "2021", "2020"]):
            recency_score = 0.60
    ev.recency_score = recency_score

    # 3. Direct Evidence Strength (Text length & concrete metrics presence)
    content_len = len(ev.content or "")
    has_numbers_or_currency = bool(re.search(r'(?:₹|INR|USD|\$|\%|\b\d+[\d,.]*\b(?:\s*(?:crore|cr|lakh|billion|million|trillion))?)', ev.content or "", re.IGNORECASE))
    direct_score = min(1.0, content_len / 400)
    if has_numbers_or_currency:
        direct_score = min(1.0, direct_score + 0.20)
    ev.direct_evidence_score = round(direct_score, 3)

    # 4. Cross-Source Score (Distinct independent publishing domains confirming facts)
    cross_score = min(1.0, 0.40 + (distinct_domain_count * 0.20))
    ev.cross_source_score = round(cross_score, 3)

    # Multi-factor formula
    final_evidence_score = (
        (ev.authority_score * 0.35) +
        (ev.relevance * 0.25) +
        (ev.recency_score * 0.15) +
        (ev.direct_evidence_score * 0.15) +
        (ev.cross_source_score * 0.10)
    )

    ev.evidence_score = round(final_evidence_score, 3)
    return ev.evidence_score


def rank_and_score_evidence(company_name: str, parameter: str, evidence_list: List[Evidence]) -> List[Evidence]:
    """
    Evaluates, ranks, and filters evidence by authority and relevance.
    Calculates distinct domain counts to power true cross-source verification.
    """
    if not evidence_list:
        return []

    distinct_domains = set(ev.source_domain for ev in evidence_list if ev.source_domain)
    domain_count = len(distinct_domains)

    scored_items: List[Tuple[float, Evidence]] = []
    for ev in evidence_list:
        score = score_evidence_item(company_name, parameter, ev, distinct_domain_count=domain_count)
        scored_items.append((score, ev))

    # Sort descending by evidence_score, then authority_tier ascending (Tier 1 first)
    scored_items.sort(key=lambda x: (x[0], -x[1].authority_tier), reverse=True)
    return [item[1] for item in scored_items]
