from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum

class ValidationStatusEnum(str, Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    INVALID = "INVALID"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"

class ProspectCandidateItem(BaseModel):
    id: str
    name: str

class ValidatedProspectAnalysisInput(BaseModel):
    prospect: str = Field(..., description="Cleaned, verified entity/company name")
    prospect_id: Optional[str] = Field(default=None, description="Canonical prospect ID from JSON")
    domain: str = Field(default="Insurance", description="Domain classification (e.g. Insurance)")
    intent: str = Field(default="prospect_analysis", description="Classification intent (e.g. prospect_analysis)")
    parameters: List[str] = Field(default_factory=list, description="Canonical normalized parameter list")
    geography: Optional[str] = Field(default="Global", description="Target geographical region")
    period: Optional[str] = Field(default="FY2024-25", description="Target reporting period")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Validation confidence score")
    mock_mode: bool = Field(default=False, description="Flag for synthetic estimation mode")

class ClarificationOption(BaseModel):
    question: str
    options: List[str]

class ValidationErrorItem(BaseModel):
    code: str
    message: str

class ValidationResultContract(BaseModel):
    valid: bool
    status: ValidationStatusEnum
    prospect: Optional[str] = None
    prospect_id: Optional[str] = None
    domain: Optional[str] = "Insurance"
    intent: Optional[str] = "prospect_analysis"
    parameters: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: Optional[str] = None
    candidates: List[Dict[str, str]] = Field(default_factory=list)
    errors: List[ValidationErrorItem] = Field(default_factory=list)
    warnings: List[ValidationErrorItem] = Field(default_factory=list)
    clarification: Optional[ClarificationOption] = None
    normalizedInput: Optional[ValidatedProspectAnalysisInput] = None
