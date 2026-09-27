"""
Research Parameters Configuration File.
Defines consolidated, high-yield research parameters and metric-specific research intents.
Optimized for precision: metric-level research intents with provider-tailored queries (Serper Google Boolean vs. Tavily NLP).
"""

from typing import Any, List
from dataclasses import dataclass, field


@dataclass
class ResearchIntent:
    """
    Encapsulates a focused research intent for a specific prospect parameter and metric.
    Decouples generic research goal from provider-specific query formatting.
    """
    company: str
    parameter: str
    metric: str
    query_type: str  # e.g., 'financial_metric', 'insurance_metric', 'regulatory', 'credit_rating', 'workforce', 'annual_report', 'technology', 'strategic_activity', 'market_analysis'
    domains: List[str] = field(default_factory=list)
    serper_query: str = ""
    tavily_query: str = ""
    trigger: str = ""
    expected_evidence: str = ""


DEFAULT_RESEARCH_PARAMETERS = {
    "Company Scale": {
        "description": (
            "Understand enterprise size and scale including annual revenue, "
            "total assets under management, employee workforce, and global/national footprint."
        ),
        "search_queries": [
            '"{company}" revenue "total assets"',
            '"{company}" AUM "assets under management"',
            '"{company}" (employees OR workforce OR headcount)',
            '"{company}" annual report financial results revenue assets'
        ],
        "preferred_sources": [
            "annual_report",
            "regulatory_filing",
            "company_website",
            "reputable_news"
        ]
    },

    "Business Growth": {
        "description": (
            "Understand commercial expansion, quarterly revenue growth, "
            "premium growth trends, customer retention, and new market penetration."
        ),
        "search_queries": [
            '"{company}" ("gross written premium" OR "revenue growth" OR "quarterly results")',
            '"{company}" ("persistency ratio" OR "customer acquisition" OR "market expansion")'
        ],
        "preferred_sources": [
            "investor_relations",
            "annual_report",
            "financial_report",
            "reputable_news"
        ]
    },

    "Market Position": {
        "description": (
            "Understand industry ranking, market share percentage, "
            "competitive moats, stock market capitalization, and brand trust."
        ),
        "search_queries": [
            '"{company}" ("market share" OR "industry ranking" OR "market position")',
            '"{company}" ("market capitalization" OR "leading insurer" OR "industry standing")'
        ],
        "preferred_sources": [
            "industry_report",
            "regulatory_source",
            "financial_news",
            "reputable_news"
        ]
    },

    "Financial Strength": {
        "description": (
            "Understand financial stability, credit ratings, solvency ratio, "
            "profit after tax (PAT), return on equity, and asset-liability management."
        ),
        "search_queries": [
            '"{company}" ("solvency ratio" OR "solvency margin") (site:irdai.gov.in OR site:crisil.com OR site:icra.in)',
            '"{company}" ("profit after tax" OR PAT OR "capital adequacy" OR "net worth")'
        ],
        "preferred_sources": [
            "credit_rating_agency",
            "regulatory_filing",
            "annual_report",
            "investor_relations"
        ]
    },

    "Insurance Performance": {
        "description": (
            "Understand underwriting discipline, gross direct premium income (GDPI), "
            "combined ratio, claims settlement ratio, and reinsurance protections."
        ),
        "search_queries": [
            '"{company}" ("combined ratio" OR "incurred claims ratio" OR "gross direct premium") (site:irdai.gov.in)',
            '"{company}" ("claims settlement ratio" OR "underwriting profit" OR "loss ratio")'
        ],
        "preferred_sources": [
            "insurance_regulator",
            "annual_report",
            "underwriting_filings",
            "industry_source"
        ]
    },

    "Operational Scale": {
        "description": (
            "Understand operational footprint including regional branch network, "
            "bancassurance bank alliances, institutional agency force, and digital touchpoints."
        ),
        "search_queries": [
            '"{company}" ("branch network" OR bancassurance OR "bank distribution partners")',
            '"{company}" ("agency workforce" OR "agent network" OR "customer service centers")'
        ],
        "preferred_sources": [
            "company_website",
            "annual_report",
            "regulatory_source",
            "reputable_news"
        ]
    },

    "Technology Activity": {
        "description": (
            "Understand digital transformation, AI/ML underwriting tools, "
            "cloud infrastructure, API integrations, and mobile self-service apps."
        ),
        "search_queries": [
            '"{company}" ("digital transformation" OR "artificial intelligence" OR "automated underwriting" OR "AI")',
            '"{company}" ("cloud infrastructure" OR "API integrations" OR "mobile app" OR insurtech)'
        ],
        "preferred_sources": [
            "technology_news",
            "press_release",
            "company_website",
            "industry_case_study"
        ]
    },

    "Strategic Activity": {
        "description": (
            "Understand major strategic initiatives, mergers & acquisitions, "
            "institutional bancassurance tie-ups, ESG framework, and corporate expansion."
        ),
        "search_queries": [
            '"{company}" ("strategic initiatives" OR partnerships OR acquisitions OR "joint ventures")',
            '"{company}" (ESG OR sustainability OR "CSR programs" OR "corporate expansion")'
        ],
        "preferred_sources": [
            "press_release",
            "annual_report",
            "reputable_news",
            "regulatory_filings"
        ]
    }
}


def build_research_intents(
    company_name: str,
    parameter: str,
    entity_profile: Any = None
) -> List[ResearchIntent]:
    """
    Generates structured metric-level ResearchIntents for a given company and parameter.
    Each intent produces provider-tailored queries (Serper Google Boolean vs. Tavily NLP).
    """
    jurisdiction = getattr(entity_profile, "jurisdiction", "IN") if entity_profile else "IN"
    official_domain = getattr(entity_profile, "official_domain", None) if entity_profile else None
    c_name = (getattr(entity_profile, "canonical_name", company_name) or company_name).strip()

    intents: List[ResearchIntent] = []

    # 1. Financial Strength
    if parameter == "Financial Strength":
        if jurisdiction == "IN":
            solvency_domains = ["irdai.gov.in", "crisil.com", "icra.in"]
            site_filter = " OR ".join(f"site:{d}" for d in solvency_domains)
            intents.append(
                ResearchIntent(
                    company=c_name,
                    parameter=parameter,
                    metric="Solvency Ratio",
                    query_type="regulatory",
                    domains=solvency_domains,
                    serper_query=f'"{c_name}" ("solvency ratio" OR "solvency margin") ({site_filter})',
                    tavily_query=f'What is the solvency ratio or solvency margin of {c_name}, and what does it indicate about the company financial strength?',
                    trigger="Solvency regulatory assessment",
                    expected_evidence="Solvency ratio figures, regulatory minimum compliance (1.5x), credit ratings"
                )
            )
            intents.append(
                ResearchIntent(
                    company=c_name,
                    parameter=parameter,
                    metric="Capital Adequacy & Profitability",
                    query_type="financial_metric",
                    domains=[],
                    serper_query=f'"{c_name}" ("profit after tax" OR PAT OR "capital adequacy" OR "net worth")',
                    tavily_query=f'What is the capital adequacy ratio, net worth, and profit after tax (PAT) of {c_name}?',
                    trigger="Profitability and balance sheet review",
                    expected_evidence="Profit after tax, balance sheet equity, capital adequacy ratio"
                )
            )
        elif jurisdiction == "US":
            intents.append(
                ResearchIntent(
                    company=c_name,
                    parameter=parameter,
                    metric="Credit Ratings & Solvency",
                    query_type="credit_rating",
                    domains=["sec.gov", "ambest.com"],
                    serper_query=f'"{c_name}" ("AM Best" rating OR "S&P" rating) ("financial strength" OR solvency)',
                    tavily_query=f'What are the AM Best and S&P financial strength credit ratings for {c_name}?',
                    trigger="US Insurance credit ratings",
                    expected_evidence="Financial strength ratings, credit outlook"
                )
            )
            intents.append(
                ResearchIntent(
                    company=c_name,
                    parameter=parameter,
                    metric="Risk-Based Capital",
                    query_type="regulatory",
                    domains=["sec.gov"],
                    serper_query=f'"{c_name}" "Form 10-K" ("balance sheet" OR "capital surplus" OR "risk based capital") site:sec.gov',
                    tavily_query=f'What is the risk-based capital and balance sheet surplus reported in {c_name} Form 10-K?',
                    trigger="SEC statutory filings",
                    expected_evidence="RBC ratio, capital surplus"
                )
            )
        elif jurisdiction in ("UK", "EU"):
            intents.append(
                ResearchIntent(
                    company=c_name,
                    parameter=parameter,
                    metric="Solvency II SFCR",
                    query_type="regulatory",
                    domains=[],
                    serper_query=f'"{c_name}" "Solvency II" SFCR ("solvency ratio" OR "capital requirement")',
                    tavily_query=f'What is the Solvency II SFCR solvency ratio and capital requirement for {c_name}?',
                    trigger="Solvency II regulatory disclosures",
                    expected_evidence="SCR coverage ratio, SFCR disclosures"
                )
            )
        else:
            intents.append(
                ResearchIntent(
                    company=c_name,
                    parameter=parameter,
                    metric="Financial Stability & Solvency",
                    query_type="financial_metric",
                    domains=[],
                    serper_query=f'"{c_name}" ("solvency ratio" OR "credit rating" OR "financial strength")',
                    tavily_query=f'What is the solvency ratio, credit rating, and overall financial stability of {c_name}?',
                    trigger="Global financial stability audit",
                    expected_evidence="Solvency metrics, credit ratings"
                )
            )

    # 2. Company Scale
    elif parameter == "Company Scale":
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Financial Scale & Revenue",
                query_type="financial_metric",
                domains=[],
                serper_query=f'"{c_name}" revenue "total assets"',
                tavily_query=f'What is the total annual revenue and balance sheet total assets of {c_name}?',
                trigger="Company financial scale assessment",
                expected_evidence="Annual revenue figures, total assets"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="AUM",
                query_type="financial_metric",
                domains=[],
                serper_query=f'"{c_name}" AUM "assets under management"',
                tavily_query=f'What are the total assets under management (AUM) of {c_name}?',
                trigger="Assets under management valuation",
                expected_evidence="AUM figures in crore/billions"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Workforce",
                query_type="workforce",
                domains=[],
                serper_query=f'"{c_name}" (employees OR workforce OR headcount)',
                tavily_query=f'What is the total employee workforce, headcount, and operational size of {c_name}?',
                trigger="Workforce and human capital scale",
                expected_evidence="Employee count, workforce numbers"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Annual Report & Financials",
                query_type="annual_report",
                domains=[],
                serper_query=f'"{c_name}" annual report financial results revenue assets',
                tavily_query=f'What do the latest annual report and financial results show for {c_name}?',
                trigger="Annual report overview",
                expected_evidence="Annual report summary metrics"
            )
        )

    # 3. Insurance Performance
    elif parameter == "Insurance Performance":
        reg_domain = ["irdai.gov.in"] if jurisdiction == "IN" else (["sec.gov"] if jurisdiction == "US" else [])
        site_filter = f"site:{reg_domain[0]}" if reg_domain else ""
        serper_q1 = f'"{c_name}" ("combined ratio" OR "incurred claims ratio" OR "gross direct premium")'
        if site_filter:
            serper_q1 = f'{serper_q1} ({site_filter})'

        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Combined & Claims Ratio",
                query_type="insurance_metric",
                domains=reg_domain,
                serper_query=serper_q1,
                tavily_query=f'What is the combined ratio, incurred claims ratio, and gross premium of {c_name}?',
                trigger="Insurance underwriting profitability",
                expected_evidence="Combined ratio percentage, claims ratio"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Claims Settlement & Loss Ratio",
                query_type="insurance_metric",
                domains=[],
                serper_query=f'"{c_name}" ("claims settlement ratio" OR "underwriting profit" OR "loss ratio")',
                tavily_query=f'What is the claims settlement ratio and underwriting loss ratio for {c_name}?',
                trigger="Claims performance analysis",
                expected_evidence="Claims settlement percentage, loss ratios"
            )
        )

    # 4. Business Growth
    elif parameter == "Business Growth":
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Premium & Revenue Growth",
                query_type="insurance_metric",
                domains=[],
                serper_query=f'"{c_name}" ("gross written premium" OR "revenue growth" OR "quarterly results")',
                tavily_query=f'What is the quarterly revenue and gross written premium growth trajectory for {c_name}?',
                trigger="Revenue and premium trajectory",
                expected_evidence="YoY growth rate, quarterly premium increase"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Customer Acquisition & Persistency",
                query_type="insurance_metric",
                domains=[],
                serper_query=f'"{c_name}" ("persistency ratio" OR "customer acquisition" OR "market expansion")',
                tavily_query=f'What is the persistency ratio and customer retention or expansion trajectory for {c_name}?',
                trigger="Policyholder persistency audit",
                expected_evidence="13th month / 61st month persistency ratio"
            )
        )

    # 5. Market Position
    elif parameter == "Market Position":
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Market Share & Ranking",
                query_type="market_analysis",
                domains=[],
                serper_query=f'"{c_name}" ("market share" OR "industry ranking" OR "market position")',
                tavily_query=f'What is the industry market share and ranking position of {c_name} compared to competitors?',
                trigger="Industry market share ranking",
                expected_evidence="Market share %, ranking among insurers"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Market Capitalization & Standing",
                query_type="market_analysis",
                domains=[],
                serper_query=f'"{c_name}" ("market capitalization" OR "leading insurer" OR "industry standing")',
                tavily_query=f'What is the market capitalization and competitive standing of {c_name} in the insurance sector?',
                trigger="Market capitalization and standing",
                expected_evidence="Market cap valuation, leadership standing"
            )
        )

    # 6. Operational Scale
    elif parameter == "Operational Scale":
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Branch Network & Bancassurance",
                query_type="operational_scale",
                domains=[],
                serper_query=f'"{c_name}" ("branch network" OR bancassurance OR "bank distribution partners")',
                tavily_query=f'What is the branch network size and bancassurance distribution partnership footprint of {c_name}?',
                trigger="Branch and bancassurance network",
                expected_evidence="Branch count, partner bank names"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Agency Workforce & Touchpoints",
                query_type="operational_scale",
                domains=[],
                serper_query=f'"{c_name}" ("agency workforce" OR "agent network" OR "customer service centers")',
                tavily_query=f'How large is the agency workforce and physical customer touchpoint network for {c_name}?',
                trigger="Agency force and regional footprint",
                expected_evidence="Agent count, service center network"
            )
        )

    # 7. Technology Activity
    elif parameter == "Technology Activity":
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Digital Transformation & AI",
                query_type="technology",
                domains=[],
                serper_query=f'"{c_name}" ("digital transformation" OR "artificial intelligence" OR "automated underwriting" OR "AI")',
                tavily_query=f'How is {c_name} utilizing artificial intelligence, digital transformation, and automated underwriting?',
                trigger="AI and digital underwriting activity",
                expected_evidence="AI tools, underwriting automation platforms"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Cloud & Platform Systems",
                query_type="technology",
                domains=[],
                serper_query=f'"{c_name}" ("cloud infrastructure" OR "API integrations" OR "mobile app" OR insurtech)',
                tavily_query=f'What core cloud platforms, API integrations, and mobile customer applications does {c_name} operate?',
                trigger="Cloud and mobile app stack",
                expected_evidence="Cloud architecture, customer app features"
            )
        )

    # 8. Strategic Activity
    elif parameter == "Strategic Activity":
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="Strategic Alliances & M&A",
                query_type="strategic_activity",
                domains=[],
                serper_query=f'"{c_name}" ("strategic initiatives" OR partnerships OR acquisitions OR "joint ventures")',
                tavily_query=f'What major strategic partnerships, mergers, acquisitions, or joint ventures has {c_name} announced?',
                trigger="Strategic M&A and alliances",
                expected_evidence="M&A deals, strategic alliances"
            )
        )
        intents.append(
            ResearchIntent(
                company=c_name,
                parameter=parameter,
                metric="ESG & Expansion Initiatives",
                query_type="strategic_activity",
                domains=[],
                serper_query=f'"{c_name}" (ESG OR sustainability OR "CSR programs" OR "corporate expansion")',
                tavily_query=f'What are the major ESG, sustainability initiatives, and corporate expansion strategies of {c_name}?',
                trigger="ESG and corporate expansion",
                expected_evidence="ESG commitments, expansion projects"
            )
        )

    # Fallback for custom / unlisted parameters
    if not intents:
        default_config = DEFAULT_RESEARCH_PARAMETERS.get(parameter, {})
        default_templates = default_config.get("search_queries", [f'"{c_name}" {parameter}'])
        for idx, template in enumerate(default_templates):
            q_formatted = template.format(company=c_name)
            intents.append(
                ResearchIntent(
                    company=c_name,
                    parameter=parameter,
                    metric=f"{parameter} Metric {idx + 1}",
                    query_type="general",
                    domains=[],
                    serper_query=q_formatted,
                    tavily_query=f"What are the key insights and details regarding {parameter} for {c_name}?",
                    trigger="Generic research probe",
                    expected_evidence=f"Disclosures relating to {parameter}"
                )
            )

    return intents


def build_serper_query(intent: ResearchIntent) -> str:
    """Returns the formatted Serper Google Boolean search query from a ResearchIntent."""
    return intent.serper_query


def build_tavily_query(intent: ResearchIntent) -> str:
    """Returns the formatted Tavily natural-language search query from a ResearchIntent."""
    return intent.tavily_query


def build_adaptive_queries(
    company_name: str,
    parameter: str,
    entity_profile: Any = None
) -> list[str]:
    """
    Constructs jurisdiction-aware, domain-targeted queries for higher retrieval precision.
    Preserved for backward-compatibility; returns formatted Serper queries from the intent pipeline.
    """
    intents = build_research_intents(company_name, parameter, entity_profile)
    return [intent.serper_query for intent in intents]

