"""
Domain Schemas Registry.
Defines dynamic parameter schemas and configuration rules for insurance domains:
- Prospect Analysis (Default)
- Proposal Analysis
- Underwriting Risk
- Claims Evaluation
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Default Domain Schemas Registry
DOMAIN_REGISTRY: Dict[str, Dict[str, Any]] = {
    "prospect_analysis": {
        "display_name": "Prospect Analysis",
        "description": "Comprehensive B2B insurance prospect evaluation across core operational and financial parameters.",
        "default_parameters": [
            "Company Scale",
            "Business Growth",
            "Market Position",
            "Financial Strength",
            "Insurance Performance",
            "Operational Scale",
            "Technology Activity",
            "Strategic Activity"
        ],
        "parameters_detail": {
            "Company Scale": {
                "description": "Enterprise size, revenue, asset base, workforce, and national/global footprint.",
                "keywords": ["scale", "revenue", "assets", "employees", "workforce", "headcount", "footprint"]
            },
            "Business Growth": {
                "description": "Commercial expansion, revenue growth, premium growth trends, and market penetration.",
                "keywords": ["growth", "expansion", "yoy", "momentum", "gwp", "quarterly results"]
            },
            "Market Position": {
                "description": "Industry ranking, market share percentage, competitive moat, and brand trust.",
                "keywords": ["position", "ranking", "market share", "competitor", "moat", "standing"]
            },
            "Financial Strength": {
                "description": "Financial stability, credit ratings, solvency ratio, PAT, and capital adequacy.",
                "keywords": ["financial", "solvency", "credit rating", "net worth", "pat", "capital"]
            },
            "Insurance Performance": {
                "description": "Underwriting discipline, GDPI, combined ratio, claims settlement, loss ratio, and reinsurance.",
                "keywords": ["insurance", "underwriting", "combined ratio", "gdpi", "claims ratio", "loss ratio"]
            },
            "Operational Scale": {
                "description": "Branch network, bancassurance alliances, institutional agency force, and distribution.",
                "keywords": ["operational", "branch", "network", "bancassurance", "agency", "distribution"]
            },
            "Technology Activity": {
                "description": "Digital transformation, AI/ML underwriting, cloud platforms, and self-service apps.",
                "keywords": ["technology", "digital", "ai", "cloud", "api", "automation"]
            },
            "Strategic Activity": {
                "description": "Strategic initiatives, M&A, partnerships, ESG framework, and corporate expansion.",
                "keywords": ["strategic", "partnership", "alliances", "merger", "acquisition", "esg"]
            }
        }
    }
}

DOMAIN_ALIASES: Dict[str, str] = {
    "prospect_analysis": "prospect_analysis",
    "insurance": "prospect_analysis"
}

def get_domain_schema(domain_name: str) -> Dict[str, Any]:
    """
    Retrieves domain schema by key.
    Raises KeyError if domain is unrecognized or unsupported (no fallback).
    """
    raw_key = domain_name.lower().strip() if domain_name else "prospect_analysis"
    key = DOMAIN_ALIASES.get(raw_key, raw_key)
    if key not in DOMAIN_REGISTRY:
        raise KeyError(f"Unsupported domain schema '{domain_name}'. Supported domain is 'prospect_analysis'.")
    return DOMAIN_REGISTRY[key]

def list_supported_domains() -> List[Dict[str, Any]]:
    """Returns list of supported domain metadata for client APIs."""
    return [
        {
            "id": domain_id,
            "display_name": schema.get("display_name"),
            "description": schema.get("description"),
            "parameters": schema.get("default_parameters", [])
        }
        for domain_id, schema in DOMAIN_REGISTRY.items()
    ]

def register_domain_schema(domain_id: str, schema_data: Dict[str, Any]) -> bool:
    """Dynamically registers a new domain schema at runtime."""
    if not domain_id or not isinstance(schema_data, dict):
        return False
    DOMAIN_REGISTRY[domain_id.lower().strip()] = schema_data
    logger.info(f"[DOMAIN SCHEMAS] Dynamically registered domain schema '{domain_id}'")
    return True
