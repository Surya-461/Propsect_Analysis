import logging
from typing import Tuple, Dict, Any
from config.domain_schemas import get_domain_schema

logger = logging.getLogger(__name__)

def validate_prospect_input(name: str, domain: str = "Insurance") -> Tuple[bool, str]:
    """
    Validates input string for prospect entity resolution using the central ProspectValidationGateway.
    Returns (is_valid, cleaned_prospect_name_or_error_msg).
    """
    from services.validation_gateway import ProspectValidationGateway
    result = ProspectValidationGateway.validate_prospect_input(
        user_input=name,
        custom_context={"domain": domain}
    )
    if result.valid and result.prospect:
        return True, result.prospect
    
    error_msg = result.reason or (result.errors[0].message if result.errors else "Please enter a valid prospect name for analysis.")
    return False, error_msg

def validate_domain_input(domain_name: str, input_payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates incoming requests against domain schema and central validation gateway.
    Returns (is_valid, cleaned_prospect_name_or_error, sanitized_payload).
    """
    target_domain = (domain_name or "Insurance").strip()
    target_name = input_payload.get("prospect_name") or input_payload.get("company_name") or ""
    
    is_valid, msg_or_name = validate_prospect_input(target_name, domain=target_domain)
    if not is_valid:
        return False, msg_or_name, {}

    sanitized = dict(input_payload)
    sanitized["prospect_name"] = msg_or_name
    sanitized["domain"] = target_domain
    
    try:
        schema = get_domain_schema(target_domain)
    except KeyError as err:
        return False, str(err).strip("'\""), {}

    extra_params = input_payload.get("extra_parameters", [])
    if extra_params and isinstance(extra_params, list):
        sanitized["extra_parameters"] = [str(p).strip() for p in extra_params if p and isinstance(p, str)]
    else:
        sanitized["extra_parameters"] = schema.get("default_parameters", [])

    return True, msg_or_name, sanitized
