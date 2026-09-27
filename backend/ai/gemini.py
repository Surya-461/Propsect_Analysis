import os
import json
import time
import socket
import logging
import threading
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("gemini_api_key")
)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()

GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "120"))

GEMINI_MAX_RETRIES = 1

MIN_GEMINI_SPACING_SECONDS = 4.0


# ============================================================
# GLOBAL REQUEST CONTROL
# ============================================================

_gemini_lock = threading.Lock()
_last_gemini_call_time = 0.0


# ============================================================
# CUSTOM EXCEPTIONS
# ============================================================

class GeminiAPIError(Exception):
    """General Gemini API error."""
    pass


class GeminiQuotaExceededError(GeminiAPIError):
    """Raised when Gemini project/model quota has been exhausted (429)."""
    pass


class GeminiModelNotFoundError(GeminiAPIError):
    """Raised when the specified Gemini model is not found / 404 NOT_FOUND."""
    pass


class GeminiAuthError(GeminiAPIError):
    """Raised when Gemini authentication / permission fails (401/403)."""
    pass


class GeminiServerError(GeminiAPIError):
    """Raised when Gemini returns a 5xx server error."""
    pass


class GeminiTimeoutError(GeminiAPIError):
    """Raised when Gemini request times out."""
    pass


class GeminiValidationError(GeminiAPIError):
    """Raised when Gemini returns an unparseable or schema-invalid response."""
    pass


# ============================================================
# HELPERS
# ============================================================

def _read_http_error_body(exc: urllib.error.HTTPError) -> str:
    """Safely read Gemini HTTP error response body."""
    try:
        return exc.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def _is_daily_quota_error(error_body: str) -> bool:
    """Detect Gemini daily/project/model quota exhaustion."""
    if not error_body:
        return False

    quota_indicators = [
        "GenerateRequestsPerDayPerProjectPerModel",
        "generate_content_free_tier_requests",
        "PerDayPerProjectPerModel",
        "daily quota",
        "quota exceeded",
        "resource_exhausted",
    ]

    error_lower = error_body.lower()
    return any(indicator.lower() in error_lower for indicator in quota_indicators)


# Import robust parsing helpers from ollama module
from ai.ollama import clean_and_parse_json, validate_analysis_response


# ============================================================
# MAIN GEMINI QUERY FUNCTION
# ============================================================

def query_gemini(
    prompt: str,
    json_output: bool = True,
    timeout: int = GEMINI_TIMEOUT,
    model_name: str = GEMINI_MODEL
) -> dict | str | None:

    global _last_gemini_call_time

    if not GEMINI_API_KEY:
        logger.error("[AI] Gemini request skipped: GEMINI_API_KEY is missing.")
        raise GeminiAuthError("GEMINI_API_KEY is missing.")

    if not prompt or not prompt.strip():
        logger.error("[AI] Gemini request skipped: empty prompt.")
        return None

    target_model = model_name or GEMINI_MODEL
    logger.info("[AI] Calling Gemini: %s", target_model)

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    if json_output:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "temperature": 0.2,
            "maxOutputTokens": 8192
        }

    data_bytes = json.dumps(payload).encode("utf-8")
    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{target_model}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    for attempt in range(GEMINI_MAX_RETRIES + 1):
        start_time = time.time()
        try:
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                response_bytes = resp.read()
                elapsed = time.time() - start_time
                logger.info("[AI] Gemini response received status=%s elapsed=%.2fs", resp.status, elapsed)

            res_json = json.loads(response_bytes.decode("utf-8"))
            candidates = res_json.get("candidates", [])

            if not candidates:
                logger.error("[AI] Gemini returned no candidates.")
                raise GeminiValidationError("Gemini response contained no candidate outputs.")

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            if not parts:
                logger.error("[AI] Gemini response contains no parts.")
                raise GeminiValidationError("Gemini candidate contained no parts.")

            # Extract and join all text parts, ignoring internal thoughts if present
            text_parts = [
                p.get("text", "") for p in parts
                if isinstance(p, dict) and not p.get("thought", False) and "text" in p
            ]
            if not text_parts:
                text_parts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]

            text_content = "".join(text_parts).strip()
            if not text_content:
                logger.error("[AI] Gemini response contains no text.")
                raise GeminiValidationError("Gemini candidate part contained no text.")

            if json_output:
                parsed_json = clean_and_parse_json(text_content)
                if parsed_json is None:
                    logger.error("[AI] Gemini returned invalid JSON response. Raw snippet: %s", text_content[:500])
                    raise GeminiValidationError("Gemini returned invalid JSON format.")
                return parsed_json

            return text_content

        except socket.timeout:
            logger.warning("[AI] Gemini socket timeout for model=%s attempt=%d", target_model, attempt + 1)
            if attempt < GEMINI_MAX_RETRIES:
                time.sleep(1.0)
                continue
            raise GeminiTimeoutError(f"Gemini request timed out for model {target_model}.")

        except urllib.error.HTTPError as exc:
            error_body = _read_http_error_body(exc)

            if exc.code == 404:
                logger.error("[AI] Gemini model unavailable: %s", target_model)
                raise GeminiModelNotFoundError(f"Gemini model unavailable: {target_model}")

            if exc.code == 429:
                if _is_daily_quota_error(error_body):
                    logger.warning("[AI] Gemini quota exceeded")
                    logger.warning("[AI] No further Gemini retries will be attempted")
                    raise GeminiQuotaExceededError("Gemini daily quota exceeded.")
                elif attempt < GEMINI_MAX_RETRIES:
                    time.sleep(2.0)
                    continue
                else:
                    raise GeminiQuotaExceededError("Gemini rate limit exceeded.")

            if exc.code in (401, 403):
                logger.error("[AI] Gemini authentication failed (HTTP %s) for model=%s", exc.code, target_model)
                raise GeminiAuthError(f"Gemini authentication failed (HTTP {exc.code}).")

            if exc.code >= 500:
                logger.error("[AI] Gemini server-side error HTTP %s for model=%s", exc.code, target_model)
                raise GeminiServerError(f"Gemini server error HTTP {exc.code}.")

            logger.error("[AI] Gemini HTTP error status=%s model=%s", exc.code, target_model)
            raise GeminiAPIError(f"Gemini HTTP error status {exc.code}.")

        except GeminiAPIError:
            raise

        except Exception as exc:
            logger.exception("[AI] Unexpected Gemini error for model=%s: %s", target_model, exc)
            raise GeminiAPIError(f"Gemini call error: {exc}")

    raise GeminiAPIError("Gemini call failed after retries.")


def summarize_analysis_with_gemini(
    company_name: str,
    evidence_by_param: dict
) -> dict:
    """
    Summarizes researched evidence across parameters using Google Gemini AI.
    """
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
                snippets.append(f"- {meta_tag} {title}: {text_piece[:1200]}")
        context_parts.append(f"### {param}\n" + ("\n".join(snippets) if snippets else "No specific disclosures found."))

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
   - Quote exact financial figures (solvency ratio, combined ratio, revenue, assets) directly from Tier 1 & 2 sources when available.
   - Never allow lower-tier general web claims to override audited regulatory schedules.
2. Executive Summary: Provide a thorough 4 to 5 sentence underwriting synthesis summarizing operational scale, primary risk exposures, and overall insurability.
3. Underwriting Verdict:
   - "overall_risk_level": Assess as "Low", "Medium", or "High" based on operational complexity, financial volatility, and risk controls.
   - "primary_exposure_classes": List 2 to 4 applicable commercial coverage classes (e.g., "Property / BI", "General Liability", "Workers Compensation", "Cyber", "Commercial Auto", "D&O / Financial Lines").
   - "entry_point_trigger": Identify a specific time-bound event (e.g., M&A, new facility opening, leadership transition, regulatory event) justifying outreach this week, or state "No immediate entry point identified".
4. Parameters:
   - CROSS-PARAMETER SYNTHESIS: Relevant enterprise disclosures (such as AUM, annual revenue, premium volume, branch count, workforce size, solvency, or credit ratings) appearing anywhere in the verified disclosures must be cross-referenced to inform related parameters (e.g., Company Scale, Business Growth, Operational Scale, Financial Strength, Market Position).
   - For each parameter, provide a 3 to 5 sentence factual summary detailing specific figures, growth rates, or operational scale. Only if there are truly no relevant public disclosures found anywhere across the company's research, state: "Insufficient Data — Not Found in Public Sources".
   - Assign "finding_classification": "Strong Fit" | "Partial Fit" | "Gap" | "Insufficient Evidence".
   - Provide up to 5 concrete empirical key facts.
5. Metrics Scorecard: Extract verified numeric metrics into the structured "metrics_scorecard" object.
6. Critical Data Gaps:
   - List 2 to 4 critical underwriting data points missing from public records that the producer should validate during discovery.

JSON SCHEMA:
{{
  "executive_summary": "4-5 sentence underwriting synthesis for {company_name} summarizing operational scale, primary risk exposures, and overall insurability.",
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
      "summary": "3-5 sentence detailed factual summary with specific figures, or 'Insufficient Data — Not Found in Public Sources'.",
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
    result = query_gemini(prompt, json_output=True, timeout=60)
    validated = validate_analysis_response(result)
    if validated:
        logger.info("[AI] Gemini response validation successful")
        return validated
    raise GeminiValidationError("Gemini did not return a valid parameters dictionary.")