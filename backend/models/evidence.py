from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Evidence(BaseModel):
    parameter: str
    title: str
    content: str
    source_url: str
    source_name: str
    source_type: str
    published_date: Optional[str] = None
    retrieved_date: Optional[str] = None
    relevance: float = 0.0

    # Extended Unified Research Schema
    source_domain: Optional[str] = None
    provider: Optional[str] = None  # e.g., "serper", "tavily", "google_news", "wikipedia", "firecrawl", "annual_report"
    authority_tier: int = 4  # Tier 1 (Highest) to Tier 5 (Lowest)
    authority_score: float = 0.50
    recency_score: float = 0.85
    direct_evidence_score: float = 0.70
    cross_source_score: float = 0.50
    evidence_score: float = 0.0
    reporting_period: Optional[str] = None  # e.g. "FY2025", "FY2024", "Q3 FY25"
    metric_data: Optional[Dict[str, Any]] = None
    metric: Optional[str] = None
    query_type: Optional[str] = None
    search_query: Optional[str] = None
    crawled_with_firecrawl: bool = False
    raw_extracted_content: Optional[str] = None
    discovered_by: List[str] = Field(default_factory=list)  # Providers that found this underlying URL
