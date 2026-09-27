import os
import json
import logging
import urllib.request
import urllib.error
import re
from socket import error as socket_error
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configurable environment variables for Ollama server and models
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434"
).rstrip("/")

PRIMARY_OLLAMA_MODEL = os.getenv(
    "PRIMARY_OLLAMA_MODEL",
    os.getenv("OLLAMA_MODEL", "qwen3:8b")
).strip() or "qwen3:8b"

FALLBACK_OLLAMA_MODEL = os.getenv(
    "FALLBACK_OLLAMA_MODEL",
    "qwen3:8b"
).strip() or "qwen3:8b"


class OllamaUnavailableError(Exception):
    """Raised when the Ollama service is unreachable or offline."""
    pass


class OllamaValidationError(Exception):
    """Raised when Ollama returns an unparseable or schema-invalid validation response."""
    pass


def is_ollama_available(timeout: int = 2) -> bool:
    """Quickly pings Ollama server /api/tags endpoint to check liveness."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_active_ollama_model() -> Optional[str]:
    """
    Detects or retrieves the configured active Ollama model.
    Checks environment preference first, then queries /api/tags for preferred models.
    """
    if PRIMARY_OLLAMA_MODEL and is_ollama_available():
        return PRIMARY_OLLAMA_MODEL

    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            if not models:
                return None
            
            for preferred in [PRIMARY_OLLAMA_MODEL, FALLBACK_OLLAMA_MODEL, "qwen3:8b", "qwen2.5:3b", "qwen2.5:1.5b", "llama3.2:3b"]:
                for m in models:
                    if preferred and preferred in m:
                        return m
            return models[0]
    except Exception:
        return None


def clean_and_parse_json(raw_text: str) -> dict | list | None:
    """
    Robust JSON parser for LLM responses.
    Handles raw JSON, markdown code fences, surrounding text, trailing commas, single quotes, and control chars.
    """
    if not raw_text or not raw_text.strip():
        return None

    text = raw_text.strip()

    # 1. Direct JSON parse attempt
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Extract content from markdown codeblock fences (```json ... ``` or ``` ... ```)
    fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fenced_match:
        fenced_content = fenced_match.group(1).strip()
        try:
            return json.loads(fenced_content)
        except Exception:
            # Try sanitizing trailing commas in fenced content
            sanitized_fenced = re.sub(r",\s*([\}\]])", r"\1", fenced_content)
            try:
                return json.loads(sanitized_fenced)
            except Exception:
                pass

    # 3. Locate outermost matching { ... } for JSON object
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1].strip()
        try:
            return json.loads(candidate)
        except Exception:
            # Sanitize trailing commas and control characters
            sanitized = re.sub(r",\s*([\}\]])", r"\1", candidate)
            sanitized = re.sub(r"[\x00-\x1f]", "", sanitized)
            try:
                return json.loads(sanitized)
            except Exception:
                pass

    # 4. Locate outermost matching [ ... ] for JSON array
    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = text[first_bracket:last_bracket + 1].strip()
        try:
            return json.loads(candidate)
        except Exception:
            sanitized = re.sub(r",\s*([\}\]])", r"\1", candidate)
            sanitized = re.sub(r"[\x00-\x1f]", "", sanitized)
            try:
                return json.loads(sanitized)
            except Exception:
                pass

    return None



def validate_analysis_response(data: Any) -> Optional[Dict[str, Any]]:
    """
    Validates and normalizes structured analysis output against expected analysis schema.
    Ensures 'parameters' dictionary and required fields are present.
    """
    if not isinstance(data, dict):
        return None

    params = None
    for k in ["parameters", "Parameters", "params", "parameter_analysis", "parameter_evaluations"]:
        if k in data:
            if isinstance(data[k], dict):
                params = data[k]
                break
            elif isinstance(data[k], list):
                # Convert list of parameter objects to dictionary keyed by parameter name
                params = {}
                for idx, item in enumerate(data[k]):
                    if isinstance(item, dict):
                        p_name = (
                            item.get("parameter_name")
                            or item.get("name")
                            or item.get("parameter")
                            or item.get("param")
                            or item.get("parameter_id")
                            or f"Parameter_{idx+1}"
                        )
                        params[p_name] = item
                if params:
                    break

    if params is None:
        candidate_params = {}
        for key, val in data.items():
            if isinstance(val, dict) and key not in (
                "executive_summary", "executiveSummary", "fit_score", "risk_rating",
                "underwriting_verdict", "underwritingVerdict", "critical_data_gaps",
                "metrics_scorecard", "metricsScorecard"
            ):
                candidate_params[key] = val
            elif isinstance(val, list) and key in ("parameter_list", "parameters_list"):
                for idx, item in enumerate(val):
                    if isinstance(item, dict):
                        p_name = item.get("parameter_name") or item.get("name") or item.get("parameter") or f"Parameter_{idx+1}"
                        candidate_params[p_name] = item
        if candidate_params:
            params = candidate_params

    if not isinstance(params, dict) or not params:
        return None

    normalized_params = {}
    for param_name, param_data in params.items():
        if isinstance(param_data, dict):
            summary = (
                param_data.get("summary")
                or param_data.get("description")
                or param_data.get("analysis")
                or param_data.get("overview")
                or param_data.get("findings")
                or ""
            )
            key_facts = (
                param_data.get("key_facts")
                or param_data.get("evidence")
                or param_data.get("facts")
                or param_data.get("observations")
                or param_data.get("insights")
                or []
            )
            if isinstance(key_facts, str):
                key_facts = [key_facts]

            finding_class = (
                param_data.get("finding_classification")
                or param_data.get("classification")
            )

            param_dict = {
                "summary": str(summary).strip(),
                "key_facts": [str(f).strip() for f in key_facts if str(f).strip()]
            }
            if finding_class:
                param_dict["finding_classification"] = str(finding_class).strip()

            normalized_params[param_name] = param_dict

    if not normalized_params:
        return None

    exec_summary = (
        data.get("executive_summary")
        or data.get("executiveSummary")
        or data.get("summary")
        or ""
    )

    result = {
        "parameters": normalized_params,
        "executive_summary": str(exec_summary).strip()
    }
    
    if "fit_score" in data:
        result["fit_score"] = data["fit_score"]
    if "risk_rating" in data:
        result["risk_rating"] = data["risk_rating"]

    if "underwriting_verdict" in data and isinstance(data["underwriting_verdict"], dict):
        result["underwriting_verdict"] = data["underwriting_verdict"]
    elif "underwritingVerdict" in data and isinstance(data["underwritingVerdict"], dict):
        result["underwriting_verdict"] = data["underwritingVerdict"]

    if "critical_data_gaps" in data and isinstance(data["critical_data_gaps"], list):
        result["critical_data_gaps"] = [str(g).strip() for g in data["critical_data_gaps"] if str(g).strip()]

    if "metrics_scorecard" in data and isinstance(data["metrics_scorecard"], dict):
        result["metrics_scorecard"] = data["metrics_scorecard"]
    elif "metricsScorecard" in data and isinstance(data["metricsScorecard"], dict):
        result["metrics_scorecard"] = data["metricsScorecard"]

    return result


def query_ollama(
    prompt: str,
    json_output: bool = True,
    timeout: int = 75,
    model_name: Optional[str] = None
) -> dict | str | None:
    """
    Queries local Ollama LLM server.
    """
    if not is_ollama_available(timeout=2):
        logger.info("[AI] Ollama service is unreachable or offline at %s", OLLAMA_BASE_URL)
        raise OllamaUnavailableError(f"Ollama server unreachable at {OLLAMA_BASE_URL}")

    target_model = model_name or get_active_ollama_model() or PRIMARY_OLLAMA_MODEL

    payload = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 3500
        }
    }

    if json_output:
        payload["format"] = "json"

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=data_bytes,
        headers={"Content-Type": "application/json"}
    )

    try:
        logger.info("[AI] Calling Local Ollama Model=%s", target_model)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            raw_text = res_data.get("response", "").strip()

            if not raw_text:
                logger.warning("[AI] %s returned empty response.", target_model)
                return None

            logger.info("[AI] Ollama response received from %s", target_model)

            if json_output:
                parsed = clean_and_parse_json(raw_text)
                if parsed is None:
                    logger.warning("[AI] %s returned invalid JSON.", target_model)
                return parsed

            return raw_text
    except (urllib.error.URLError, socket_error) as exc:
        logger.warning("[AI] Ollama server connection failed for %s: %s", target_model, exc)
        raise OllamaUnavailableError(f"Ollama server unreachable for model {target_model}: {exc}")
    except Exception as exc:
        logger.warning("[AI] Ollama query error for %s: %s", target_model, exc)
        return None


def summarize_analysis_with_ollama(
    company_name: str,
    evidence_by_param: Dict[str, Any],
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Summarizes researched evidence across parameters using local Ollama model.
    """
    target_model = model_name or PRIMARY_OLLAMA_MODEL

    context_parts = []
    for param, ev_list in evidence_by_param.items():
        snippets = []
        for ev in (ev_list or [])[:5]:
            title = getattr(ev, 'title', '') or ''
            content = getattr(ev, 'content', '') or ''
            tier_num = getattr(ev, 'authority_tier', 4) or 4
            tier_label = "STATUTORY" if tier_num == 1 else ("CREDIT RATING" if tier_num == 2 else ("OFFICIAL" if tier_num == 3 else "NEWS/WEB"))
            period = getattr(ev, 'reporting_period', None)
            period_str = f" | Period: {period}" if period else ""
            source_name = getattr(ev, 'source_name', 'Public Source') or 'Public Source'
            meta_tag = f"[TIER {tier_num} {tier_label}{period_str} | {source_name}]"

            if content or title:
                text_piece = content if content and len(content) > len(title) else title
                snippets.append(f"- {meta_tag} {title}: {text_piece[:850]}")
        context_parts.append(f"### {param}\n" + ("\n".join(snippets) if snippets else "No specific snippets."))

    evidence_text = "\n\n".join(context_parts)

    prompt = f"""You are a Senior Commercial Insurance Underwriting Strategist and Prospect Intelligence Specialist.
Analyze the following verified public disclosures for {company_name}:

{evidence_text}

MISSION:
Perform an exhaustive commercial insurance prospect analysis covering risk posture, coverage exposures, and broker entry-point signals.
Translate raw disclosures into concrete underwriting insights (facility/workforce scale, solvency/liquidity, loss history, cyber/tech footprint, and trigger events).

OPERATIONAL GUIDELINES:
1. AUTHORITY DIRECTIVE:
   - Tier 1 (Statutory Filings / Regulators) and Tier 2 (Credit Rating Agencies) are GROUND TRUTH.
   - Extract exact financial figures (solvency ratio, combined ratio, revenue, assets) directly from Tier 1 & 2 sources when available.
   - Never allow lower-tier general web claims to override audited regulatory schedules.
2. Executive Summary: Provide a thorough 3 to 5 sentence underwriting synthesis summarizing operational scale, primary risk exposures, and overall insurability.
3. Underwriting Verdict:
   - "overall_risk_level": Assess as "Low", "Medium", or "High".
   - "primary_exposure_classes": List 2 to 4 commercial coverage classes (e.g., "Property / BI", "General Liability", "Workers Compensation", "Cyber", "Commercial Auto", "D&O / Financial Lines").
   - "entry_point_trigger": Identify a specific time-bound event (e.g., M&A, new facility opening, leadership transition, regulatory event) justifying outreach, or state "No immediate entry point identified".
4. Parameters:
   - CROSS-PARAMETER SYNTHESIS: Relevant enterprise disclosures (such as AUM, annual revenue, premium volume, branch count, workforce size, solvency, or credit ratings) appearing anywhere in the verified disclosures must be cross-referenced to inform related parameters (e.g., Company Scale, Business Growth, Operational Scale, Financial Strength, Market Position).
   - For each parameter, provide a 2 to 4 sentence factual summary detailing specific figures or operational scale. Only if there are truly no relevant public disclosures found anywhere across the company's research, state: "Insufficient Data — Not Found in Public Sources".
   - Assign "finding_classification": "Strong Fit" | "Partial Fit" | "Gap" | "Insufficient Evidence".
   - Provide up to 5 concrete empirical key facts.
5. Metrics Scorecard: Extract verified numeric metrics into the structured "metrics_scorecard" object.
6. Critical Data Gaps:
   - List 2 to 3 critical underwriting data points missing from public records to validate during discovery.

JSON SCHEMA:
{{
  "executive_summary": "3-5 sentence underwriting synthesis for {company_name} summarizing operational scale, primary risk exposures, and overall insurability.",
  "underwriting_verdict": {{
    "overall_risk_level": "Low | Medium | High",
    "primary_exposure_classes": ["Property / BI", "General Liability", "Workers Compensation", "Cyber"],
    "entry_point_trigger": "Identified time-bound event justifying outreach, or 'No immediate entry point identified'."
  }},
  "metrics_scorecard": {{
    "solvency_ratio": {{
      "value": "e.g. 1.95x or 'Not Disclosed'",
      "status": "Strong | Adequate | Deficient | Unverified",
      "period": "e.g. FY24 or 'Current'",
      "source": "Name of source filing"
    }},
    "combined_ratio": {{
      "value": "e.g. 93.5% or 'Not Disclosed'",
      "status": "Underwriting Profit (<100%) | Loss (>100%) | Unverified",
      "period": "e.g. FY24 or 'Current'",
      "source": "Name of source filing"
    }},
    "gross_written_premium": {{
      "value": "e.g. $15.2B or ₹12,400 Cr or 'Not Disclosed'",
      "growth_yoy": "e.g. +14.8% or 'Not Disclosed'"
    }},
    "credit_rating": {{
      "agency": "e.g. AM Best | CRISIL | S&P or 'None'",
      "grade": "e.g. AAA / A+ or 'Not Disclosed'",
      "outlook": "Stable | Positive | Negative | Unverified"
    }}
  }},
  "parameters": {{
    "<Parameter Name>": {{
      "summary": "2-4 sentence detailed factual summary with specific figures, or 'Insufficient Data — Not Found in Public Sources'.",
      "finding_classification": "Strong Fit | Partial Fit | Gap | Insufficient Evidence",
      "key_facts": [
        "Observation 1 (concrete metric/date)",
        "Observation 2"
      ]
    }}
  }},
  "critical_data_gaps": [
    "Key underwriting information missing from public disclosures to validate in discovery"
  ]
}}
"""
    result = query_ollama(prompt, json_output=True, timeout=180, model_name=target_model)
    validated = validate_analysis_response(result)
    if validated:
        logger.info("[AI] Ollama response validation successful for %s", target_model)
        return validated
    
    raise OllamaValidationError(f"Ollama model {target_model} did not return a valid parameters dictionary.")
