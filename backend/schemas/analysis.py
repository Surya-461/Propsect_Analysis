from pydantic import BaseModel
from typing import List

class SourceEvidence(BaseModel):
    name: str
    url: str
    evidence: str

class ParameterAnalysis(BaseModel):
    parameter: str
    summary: str
    key_facts: List[str]
    sources: List[SourceEvidence]
    confidence: str = "High"
