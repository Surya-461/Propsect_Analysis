"""
Proposal Analysis Configuration Catalog.
Defines canonical parameters, metadata, search hooks, and scoring tiers
for Proposal-Based Prospect Analysis.
"""

import os
from typing import Dict, List, Any

# Configurable worker-pool concurrency limit (master catalog contains 15 parameters)
PROPOSAL_MAX_CONCURRENT_PARAMETERS: int = int(os.environ.get("PROPOSAL_MAX_CONCURRENT_PARAMETERS", "15"))

FIT_TIERS = [
    {"min_score": 81, "max_score": 100, "fit_level": "Very High Fit", "short_label": "Very High"},
    {"min_score": 61, "max_score": 80, "fit_level": "High Fit", "short_label": "High"},
    {"min_score": 41, "max_score": 60, "fit_level": "Moderate Fit", "short_label": "Moderate"},
    {"min_score": 21, "max_score": 40, "fit_level": "Low Fit", "short_label": "Low"},
    {"min_score": 0, "max_score": 20, "fit_level": "Very Low Fit", "short_label": "Very Low"},
]

def score_to_fit_level(score: int) -> str:
    """Returns the fit level string for a given 0-100 numerical score."""
    clamped = max(0, min(100, int(round(score))))
    for tier in FIT_TIERS:
        if tier["min_score"] <= clamped <= tier["max_score"]:
            return tier["fit_level"]
    return "Moderate Fit"

def score_to_short_fit(score: int) -> str:
    """Returns the short fit label (e.g. 'Very High', 'High') for a parameter score."""
    clamped = max(0, min(100, int(round(score))))
    for tier in FIT_TIERS:
        if tier["min_score"] <= clamped <= tier["max_score"]:
            return tier["short_label"]
    return "Moderate"


PROPOSAL_PARAMETERS_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "business_alignment",
        "name": "Business Alignment",
        "category": "Prospect Fit",
        "description": "How closely the prospect's overall business model, commercial lines, and target markets align with the proposal.",
        "search_queries": [
            "{company} commercial insurance lines business model overview annual report",
            "{company} core business operations enterprise insurance portfolio"
        ],
        "default_recommended": False,
        "keywords": ["commercial", "business", "enterprise", "portfolio", "lines of business", "corporate"]
    },
    {
        "id": "insurance_product_alignment",
        "name": "Insurance Product Alignment",
        "category": "Domain Fit",
        "description": "Alignment between the proposal's product scope (property, casualty, life, cyber, health) and the prospect's existing product offerings.",
        "search_queries": [
            "{company} insurance products commercial lines policy offerings coverage",
            "{company} insurance underwriting portfolio products specialties"
        ],
        "default_recommended": False,
        "keywords": ["product", "coverage", "policy", "casualty", "property", "cyber", "life", "health"]
    },
    {
        "id": "underwriting_relevance",
        "name": "Underwriting Relevance",
        "category": "Business Need",
        "description": "Relevance of the proposal to the prospect's underwriting operations, appetite, pricing discipline, and risk intake.",
        "search_queries": [
            "{company} underwriting operations risk assessment guidelines portfolio appetite",
            "{company} underwriting combined ratio loss ratio pricing discipline"
        ],
        "default_recommended": False,
        "keywords": ["underwriting", "risk assessment", "pricing", "loss ratio", "combined ratio", "intake"]
    },
    {
        "id": "claims_relevance",
        "name": "Claims Relevance",
        "category": "Operations",
        "description": "Relevance of the proposal to claims processing, adjudication speed, fraud detection, and settlement operations.",
        "search_queries": [
            "{company} claims settlement ratio claims processing turnaround automation",
            "{company} claims management digital adjudication fraud detection"
        ],
        "default_recommended": False,
        "keywords": ["claims", "adjudication", "settlement", "payout", "claim turnaround", "dispute"]
    },
    {
        "id": "ai_ml_adoption",
        "name": "AI / ML Adoption",
        "category": "Technology",
        "description": "Evidence of AI/ML adoption, predictive analytics, intelligent automation, or strategic investments in cognitive technologies.",
        "search_queries": [
            "{company} artificial intelligence machine learning generative ai adoption",
            "{company} ai underwriting automation algorithms machine learning initiatives"
        ],
        "default_recommended": False,
        "keywords": ["ai", "artificial intelligence", "machine learning", "ml", "algorithms", "automation", "cognitive"]
    },
    {
        "id": "digital_transformation",
        "name": "Digital Transformation",
        "category": "Technology",
        "description": "Evidence of digital transformation programs, cloud migrations, modern portal rollouts, and customer journey digitization.",
        "search_queries": [
            "{company} digital transformation strategy cloud migration modernization",
            "{company} digital roadmap it investment platform transformation"
        ],
        "default_recommended": False,
        "keywords": ["digital transformation", "cloud", "digitalization", "platform", "modernization roadmap"]
    },
    {
        "id": "technology_modernization",
        "name": "Technology Modernization",
        "category": "Technology",
        "description": "Evidence of core IT modernization, legacy platform replacement, API-first architecture, and modern core system adoption.",
        "search_queries": [
            "{company} core insurance platform modernization guidewire duck creek api",
            "{company} enterprise architecture technology stack it modernization"
        ],
        "default_recommended": False,
        "keywords": ["modernization", "core system", "legacy", "api", "architecture", "microservices", "it stack"]
    },
    {
        "id": "data_analytics",
        "name": "Data & Analytics",
        "category": "Technology",
        "description": "Relevance and maturity of enterprise data lakes, actuarial analytics, telemetry, and portfolio business intelligence.",
        "search_queries": [
            "{company} data analytics telemetry actuarial modeling data warehouse",
            "{company} big data predictive modeling portfolio analytics intelligence"
        ],
        "default_recommended": False,
        "keywords": ["data", "analytics", "data warehouse", "telemetry", "business intelligence", "predictive"]
    },
    {
        "id": "strategic_initiative",
        "name": "Strategic Initiative",
        "category": "Strategy",
        "description": "Evidence that the proposal directly supports corporate strategic priorities, executive goals, or announced multi-year roadmaps.",
        "search_queries": [
            "{company} strategic priorities corporate strategy annual report executive roadmap",
            "{company} strategic partnership innovation expansion roadmap"
        ],
        "default_recommended": False,
        "keywords": ["strategy", "strategic initiative", "executive priority", "vision", "roadmap", "investor day"]
    },
    {
        "id": "financial_capacity",
        "name": "Financial Capacity",
        "category": "Financial",
        "description": "Prospect's financial scale, balance sheet health, capital surplus, solvency margin, and capability to fund multi-million investments.",
        "search_queries": [
            "{company} solvency ratio credit rating total assets financial strength net worth",
            "{company} annual report revenue profit after tax balance sheet capital adequacy"
        ],
        "default_recommended": False,
        "keywords": ["financial capacity", "solvency", "capital", "budget", "balance sheet", "net worth", "investment"]
    },
    {
        "id": "growth_expansion",
        "name": "Growth / Expansion",
        "category": "Business Signals",
        "description": "Commercial growth signals, gross written premium (GWP) expansion, regional diversification, and active market share acquisition.",
        "search_queries": [
            "{company} gross direct premium income gross written premium YoY growth quarterly",
            "{company} market share expansion new market entry business growth"
        ],
        "default_recommended": False,
        "keywords": ["growth", "expansion", "gwp", "gdpi", "market share", "organic growth", "yoy"]
    },
    {
        "id": "implementation_fit",
        "name": "Implementation Fit",
        "category": "Solution Fit",
        "description": "Operational feasibility, organizational readiness, partner integration ecosystem, and delivery timeline alignment for the proposed solution.",
        "search_queries": [
            "{company} implementation partner vendor technology deployment integration",
            "{company} technology operational rollout capabilities it organization"
        ],
        "default_recommended": False,
        "keywords": ["implementation", "feasibility", "integration", "deployment", "vendor", "readiness"]
    },
    {
        "id": "opportunity_timing",
        "name": "Opportunity Timing",
        "category": "Buying Signal",
        "description": "Evidence indicating potential timing, procurement cycles, executive leadership turnover, technology obsolescence, or urgent business triggers.",
        "search_queries": [
            "{company} technology procurement executive appointment rfp announcement",
            "{company} modernization contract renewal vendor selection timeframe"
        ],
        "default_recommended": False,
        "keywords": ["timing", "procurement", "urgency", "contract renewal", "rfp", "modernization timing"]
    },
    {
        "id": "regulatory_compliance",
        "name": "Regulatory / Compliance Fit",
        "category": "Risk",
        "description": "Relevance of insurance regulatory compliance (IRDAI, Solvency II, NAIC, EIOPA), statutory reporting, data privacy, and governance requirements.",
        "search_queries": [
            "{company} regulatory compliance statutory filings irda regulatory audit",
            "{company} data privacy compliance dpdp governance risk reporting"
        ],
        "default_recommended": False,
        "keywords": ["regulatory", "compliance", "irdai", "solvency ii", "governance", "statutory", "audit", "data privacy"]
    },
    {
        "id": "competitive_landscape",
        "name": "Competitive Landscape",
        "category": "Market",
        "description": "Market positioning, competitive moat, peer group benchmarking, and defensive or offensive pressures relevant to the proposed solution.",
        "search_queries": [
            "{company} competitors market ranking peer comparison competitive advantage",
            "{company} market leadership competitive benchmark industry position"
        ],
        "default_recommended": False,
        "keywords": ["competitors", "competitive landscape", "market ranking", "peers", "market leadership", "benchmarking"]
    }
]

PROPOSAL_PARAMETERS_BY_ID: Dict[str, Dict[str, Any]] = {
    param["id"]: param for param in PROPOSAL_PARAMETERS_CATALOG
}
