from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ProspectRequest(BaseModel):
    prospect_name: str
    company_name: Optional[str] = None
    domain: Optional[str] = "Insurance"
    mock_mode: Optional[bool] = False
    extra_parameters: Optional[List[str]] = None

class ProspectValidationRequest(BaseModel):
    prospect_name: str
    domain: Optional[str] = "Insurance"

class ChatRequest(BaseModel):
    analysis_id: Optional[int] = None
    client_message_id: Optional[str] = None
    prospect_name: Optional[str] = None
    company_name: Optional[str] = None
    question: str
    parameter: Optional[str] = None
    domain: Optional[str] = "Insurance"
    report_data: Optional[Dict[str, Any]] = None
    active_prospect_name: Optional[str] = None
    active_prospect_id: Optional[str] = None
    switch_confirmed: Optional[bool] = False
    switch_to_prospect: Optional[str] = None
    switch_to_prospect_id: Optional[str] = None
    stay_confirmed: Optional[bool] = False
    pending_question: Optional[str] = None
    pending_parameter: Optional[str] = None
    mock_mode: Optional[bool] = False
