import logging
from typing import List, Tuple, Any, Dict
from models.evidence import Evidence
from research.query_cache import GLOBAL_RESEARCH_CACHE
from research.normalizer import deduplicate_evidence
from research.authority_ranker import rank_and_score_evidence
from research.conflict_resolver import curate_evidence_with_conflict_resolution
from research.collectors import (
    collect_tavily_evidence,
    collect_serper_evidence,
    collect_google_news_evidence,
    collect_wikipedia_evidence,
    collect_financial_evidence,
    collect_industry_news_evidence,
    collect_regulatory_evidence,
    enrich_evidence_with_crawler
)

logger = logging.getLogger(__name__)


from config.research_parameters import ResearchIntent, build_research_intents

# Source Grouping Engine: clusters parameters sharing identical reporting repositories
PARAMETER_SOURCE_GROUPS: Dict[str, str] = {
    "Financial Strength": "financials",
    "Company Scale": "financials",
    "Business Growth": "financials",
    "financial_strength": "financials",
    "operational_scale": "insurance_operations",
    "Operational Scale": "insurance_operations",
    "Insurance Performance": "insurance_operations",
    "claims_relevance": "insurance_operations",
    "underwriting_relevance": "insurance_operations",
    "Technology Activity": "technology",
    "digital_transformation": "technology",
    "ai_ml_adoption": "technology",
    "security_compliance": "security_and_governance",
    "regulatory_statutory_compliance": "security_and_governance",
    "Market Position": "market_strategy",
    "Strategic Activity": "market_strategy",
    "business_alignment": "market_strategy",
    "insurance_product_alignment": "market_strategy"
}

def _normalize_query_str(q: str) -> str:
    """Removes extra whitespace and normalizes query text for deduplication."""
    return " ".join(q.strip().split()).lower()


def route_and_execute_research(
    company_name: str,
    parameter: str,
    search_queries: List[Any] | None = None,
    preferred_sources: List[str] | None = None,
    max_queries: int = 2,
    research_intents: List[ResearchIntent] | None = None
) -> Tuple[List[Evidence], List[str]]:
    """
    Intelligent Multi-Stage Research Router & Evidence Curation Pipeline.
    
    Stages:
    1. Cache Probe: check if recent prospect+parameter queries exist in cache.
    2. Primary Discovery: query Tavily (NLP + include_domains), Serper.dev (Google Boolean), and collectors.
    3. URL Normalization & Deduplication (merging cross-engine discovery metadata).
    4. Tiered Authority Classification & Parameter Priority Ranking.
    5. WebCrawlerAPI Deep Content Extraction on top-ranked authoritative pages.
    6. Period-Aware Conflict Resolution (No Averaging).
    7. Caching & Return.
    """
    cache_key = f"{company_name}:{parameter}"
    cached_items = GLOBAL_RESEARCH_CACHE.get("param_research", cache_key)
    if cached_items:
        return cached_items, []

    # Check shared group cache to reuse evidence from companion parameters
    source_group = PARAMETER_SOURCE_GROUPS.get(parameter)
    if source_group:
        group_cache_key = f"{company_name}:group:{source_group}"
        group_cached = GLOBAL_RESEARCH_CACHE.get("param_research", group_cache_key)
        if group_cached and len(group_cached) >= 3:
            # Re-rank group evidence specifically for this parameter
            ranked_group_items = rank_and_score_evidence(company_name, parameter, group_cached)
            if ranked_group_items:
                GLOBAL_RESEARCH_CACHE.set("param_research", cache_key, ranked_group_items[:8])
                return ranked_group_items[:8], []

    raw_evidence: List[Evidence] = []
    param_lower = parameter.lower()

    # -------------------------------------------------------------------------
    # STAGE 1: Primary Search Engines (Tavily + Serper) & Metric Research Intents
    # -------------------------------------------------------------------------
    # Resolve intents if not explicitly provided
    active_intents: List[ResearchIntent] = []
    if research_intents and isinstance(research_intents, list):
        active_intents = [i for i in research_intents if isinstance(i, ResearchIntent)]
    elif search_queries:
        for item in search_queries:
            if isinstance(item, ResearchIntent):
                active_intents.append(item)
            elif isinstance(item, str):
                formatted_q = item.format(company=company_name)
                active_intents.append(
                    ResearchIntent(
                        company=company_name,
                        parameter=parameter,
                        metric=parameter,
                        query_type="general",
                        domains=[],
                        serper_query=formatted_q,
                        tavily_query=f"What are the key details and disclosures regarding {parameter} for {company_name}?"
                    )
                )

    if not active_intents:
        active_intents = build_research_intents(company_name, parameter)

    executed_queries: set[tuple[str, str]] = set()

    for intent in active_intents[:max_queries]:
        serper_q = intent.serper_query.strip()
        tavily_q = intent.tavily_query.strip()
        norm_serper = _normalize_query_str(serper_q)
        norm_tavily = _normalize_query_str(tavily_q)

        # 1. Primary: Tavily AI Search (Natural Language + Native Domain Filtering)
        if tavily_q and ("tavily", norm_tavily) not in executed_queries:
            executed_queries.add(("tavily", norm_tavily))
            try:
                tavily_results = collect_tavily_evidence(
                    query=tavily_q,
                    parameter=parameter,
                    max_results=4,
                    include_domains=intent.domains,
                    prospect_name=company_name,
                    metric=intent.metric,
                    query_type=intent.query_type
                )
                raw_evidence.extend(tavily_results)
            except Exception as e:
                logger.warning(f"Search Router: Tavily execution failed for '{tavily_q}': {e}")

        # 2. Primary: Serper.dev Google Search API (Quoted entity + Boolean operators + site:)
        if serper_q and ("serper", norm_serper) not in executed_queries:
            executed_queries.add(("serper", norm_serper))
            try:
                serper_results = collect_serper_evidence(
                    query=serper_q,
                    parameter=parameter,
                    max_results=4,
                    prospect_name=company_name,
                    metric=intent.metric,
                    query_type=intent.query_type
                )
                raw_evidence.extend(serper_results)
            except Exception as e:
                logger.warning(f"Search Router: Serper execution failed for '{serper_q}': {e}")

        # 3. Google News RSS Collector
        if serper_q and ("google_news", norm_serper) not in executed_queries:
            executed_queries.add(("google_news", norm_serper))
            try:
                news_results = collect_google_news_evidence(serper_q, parameter)
                for ev in news_results:
                    ev.metric = intent.metric
                    ev.query_type = "news"
                raw_evidence.extend(news_results)
            except Exception as e:
                logger.warning(f"Search Router: Google News execution failed: {e}")

    # -------------------------------------------------------------------------
    # STAGE 2: Existing Domain-Specific Knowledge Collectors (Preserved)
    # -------------------------------------------------------------------------
    if "scale" in param_lower or "operational" in param_lower:
        raw_evidence.extend(collect_wikipedia_evidence(company_name, parameter))
    elif "financial" in param_lower or "growth" in param_lower:
        raw_evidence.extend(collect_financial_evidence(company_name, parameter))
    elif "insurance" in param_lower:
        raw_evidence.extend(collect_regulatory_evidence(company_name, parameter))
        raw_evidence.extend(collect_industry_news_evidence(company_name, parameter))
    elif "market" in param_lower or "strategic" in param_lower:
        raw_evidence.extend(collect_industry_news_evidence(company_name, parameter))
        raw_evidence.extend(collect_wikipedia_evidence(company_name, parameter))
    elif "technology" in param_lower:
        raw_evidence.extend(collect_industry_news_evidence(company_name, parameter))

    # -------------------------------------------------------------------------
    # STAGE 3: URL Normalization & Deduplication
    # -------------------------------------------------------------------------
    deduped = deduplicate_evidence(raw_evidence)

    # -------------------------------------------------------------------------
    # STAGE 4: Source Authority Classification & Parameter-Specific Ranking
    # -------------------------------------------------------------------------
    from research.source_manager import is_relevant_evidence
    relevant_items = [ev for ev in deduped if is_relevant_evidence(company_name, ev)]
    ranked_items = rank_and_score_evidence(company_name, parameter, relevant_items)

    # Filter by minimum evidence score threshold (>= 0.40)
    top_candidates = [ev for ev in ranked_items if ev.evidence_score >= 0.40]
    if not top_candidates:
        top_candidates = ranked_items[:3]

    # -------------------------------------------------------------------------
    # STAGE 5: Optional WebCrawlerAPI enrichment with free fallback
    # Keep the number of deep scrapes intentionally low to control paid usage.
    # -------------------------------------------------------------------------
    enriched_items = enrich_evidence_with_crawler(
        evidence_list=top_candidates[:5],
        max_crawl=1,
        min_authority_tier=3
    )

    # -------------------------------------------------------------------------
    # STAGE 6: Period-Aware Conflict Resolution (No Averaging)
    # -------------------------------------------------------------------------
    curated_items, conflict_disclosures = curate_evidence_with_conflict_resolution(enriched_items)
    final_evidence = curated_items[:8]

    # -------------------------------------------------------------------------
    # STAGE 7: Cache Verified Evidence (Parameter + Shared Source Group)
    # -------------------------------------------------------------------------
    if final_evidence:
        GLOBAL_RESEARCH_CACHE.set("param_research", cache_key, final_evidence)
        if source_group:
            group_cache_key = f"{company_name}:group:{source_group}"
            existing_group = GLOBAL_RESEARCH_CACHE.get("param_research", group_cache_key) or []
            combined_group = deduplicate_evidence(list(final_evidence) + list(existing_group))
            GLOBAL_RESEARCH_CACHE.set("param_research", group_cache_key, combined_group[:15])

    return final_evidence, conflict_disclosures
