from pydantic import BaseModel, Field
from typing import List, Optional

class ComparisonRequest(BaseModel):
    prospects: List[str] = Field(..., min_length=2, max_length=3, description="List of 2 to 3 prospect names to compare")
    domain: Optional[str] = "Insurance"
    mock_mode: Optional[bool] = False

class CarrierBenchmarkMetrics(BaseModel):
    company_name: str
    solvency_ratio: str
    combined_ratio: str
    aum_scale: str
    premium_growth: str
    market_position: str
    digital_maturity: str
    credit_rating: str
    overall_score: int
