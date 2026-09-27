from models.evidence import Evidence

def collect_regulatory_evidence(company_name: str, parameter: str) -> list[Evidence]:
    """
    Collects regulatory and compliance filing indicators.
    Returns empty list if no real external regulatory filings are retrieved.
    """
    return []
