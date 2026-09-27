import os
import json
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
INTENT_CONFIG_PATH = os.path.join(CONFIG_DIR, "intent_config.json")

# In-memory cache for dynamic config with mtime check
_CONFIG_CACHE: Dict[str, Any] = {}
_LAST_MTIME: float = 0.0

DEFAULT_FALLBACK_CONFIG = {
    "greeting_triggers": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"],
    "default_greeting_response": "Hello! How can I assist you with your prospect analysis today?",
    "greeting_rules": [
        {
            "triggers": ["how does this system work", "how does it work"],
            "response": "Prospect AI is a B2B Underwriting & Intelligence Platform. Enter any insurance prospect name to generate a multi-source 8-parameter underwriting dossier grounded in verified disclosures."
        },
        {
            "triggers": ["what parameters", "which parameters", "supported parameters"],
            "response": "I can analyze 8 core underwriting parameters: Financial Strength, Insurance Performance, Technology Activity, Company Scale, Business Growth, Market Position, Operational Scale, and Strategic Activity."
        },
        {
            "triggers": ["thank you", "thanks", "thank you so much", "thx"],
            "response": "You're welcome! Let me know if you need further underwriting intelligence."
        }
    ],
    "unsupported_triggers": [
        "book a flight", "book flight", "hotel reservation", "order food", "weather forecast", "send email", "private password"
    ],
    "unsupported_response": "I specialize in B2B prospect analysis and underwriting intelligence. I cannot perform external tasks such as flight bookings or non-business actions.",
    "parameter_vocabulary_map": {
        "Company Scale": ["company scale", "scale", "revenue", "asset", "headcount", "employees", "workforce", "valuation", "enterprise"],
        "Business Growth": ["business growth", "growth", "expansion", "trajectory", "yoy", "momentum", "premium growth"],
        "Market Position": ["market position", "market share", "ranking", "position", "competitor", "moat", "peer"],
        "Financial Strength": ["financial strength", "financial", "solvency", "capital adequacy", "roe", "pat", "net worth", "aum", "profitability"],
        "Insurance Performance": ["insurance performance", "insurance", "underwriting", "combined ratio", "gwp", "gross written premium", "claims", "loss ratio", "persistency"],
        "Operational Scale": ["operational scale", "operational", "branch", "distribution", "agency", "agents", "footprint", "network"],
        "Technology Activity": ["technology activity", "technology", "tech", "digital", "ai", "cloud", "automation", "rpa", "chatbot"],
        "Strategic Activity": ["strategic activity", "strategic", "partnership", "alliances", "m&a", "acquisition", "product launch", "launch"]
    }
}


def load_intent_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Dynamically loads intent configuration from backend/config/intent_config.json.
    Automatically invalidates cache if file modification timestamp (mtime) changes.
    """
    global _CONFIG_CACHE, _LAST_MTIME

    current_mtime = 0.0
    if os.path.exists(INTENT_CONFIG_PATH):
        try:
            current_mtime = os.path.getmtime(INTENT_CONFIG_PATH)
        except OSError:
            current_mtime = 0.0

    if not force_reload and _CONFIG_CACHE and current_mtime == _LAST_MTIME and current_mtime > 0:
        return _CONFIG_CACHE

    config = dict(DEFAULT_FALLBACK_CONFIG)

    # 1. Load primary intent_config.json
    if os.path.exists(INTENT_CONFIG_PATH):
        try:
            with open(INTENT_CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded_json = json.load(f)
                if isinstance(loaded_json, dict):
                    config.update(loaded_json)
        except Exception as e:
            logger.error(f"Error loading dynamic intent config from {INTENT_CONFIG_PATH}: {e}")

    _CONFIG_CACHE = config
    _LAST_MTIME = current_mtime
    return _CONFIG_CACHE


def is_general_chat_greeting(question: str, custom_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Dynamically evaluates if the input question matches greeting triggers or rules.
    Does NOT match if the message contains a substantive business, parameter, or entity inquiry.
    """
    q = (question or "").lower().strip()
    if not q:
        return None

    # Guard: if the message contains substantive inquiry terms or is a question with depth,
    # let it pass through to the conversational analysis pipeline
    substantive_terms = {
        "what", "how", "why", "who", "which", "where", "tell", "show", "give", "explain",
        "solvency", "ratio", "revenue", "premium", "claims", "loss", "growth", "strength",
        "market", "share", "rating", "assets", "aum", "scale", "performance", "risk", "tech",
        "compliance", "detail", "compare", "versus", "vs", "evidence", "source", "sources",
        "prospect", "insurance", "underwriting", "policy", "cover", "coverage"
    }
    words = set(re.findall(r'\b[a-z0-9]+\b', q))
    if words.intersection(substantive_terms) and len(words) > 2:
        return None

    config = custom_config or load_intent_config()

    # 1. Check dynamic greeting rules first (e.g. "how does this system work")
    greeting_rules = config.get("greeting_rules", [])
    for rule in greeting_rules:
        triggers = rule.get("triggers", [])
        if any(tr.lower() in q for tr in triggers):
            return rule.get("response")

    # 2. Check greeting triggers (exact word boundaries for short greeting statements)
    greeting_triggers = config.get("greeting_triggers", [])
    for t in greeting_triggers:
        t_clean = t.lower().strip()
        if t_clean and re.search(r'\b' + re.escape(t_clean) + r'\b', q) and len(words) <= 4:
            return config.get("default_greeting_response", "Hello! How can I assist you with your prospect analysis today?")

    return None


def is_unsupported_request(question: str, custom_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Dynamically evaluates if the question contains unsupported non-underwriting request triggers.
    Allows insurance and corporate inquiries (e.g. hotel liability, aviation/flight insurance).
    """
    q = (question or "").lower().strip()
    if not q:
        return None

    config = custom_config or load_intent_config()
    unsupported_phrases = config.get("unsupported_triggers", []) + [
        "book a flight", "book flight", "book a hotel", "hotel reservation",
        "weather forecast", "what is the weather", "order food", "tell me a joke",
        "tell a joke"
    ]

    for kw in unsupported_phrases:
        kw_clean = kw.lower().strip()
        if kw_clean and kw_clean in q:
            return config.get(
                "unsupported_response",
                "I specialize in B2B prospect analysis and underwriting intelligence. I cannot perform external tasks such as flight bookings or non-business actions."
            )

    return None


def detect_parameter_match(
    question: str,
    explicit_param: Optional[str] = None,
    vocabulary_map: Optional[Dict[str, List[str]]] = None
) -> Optional[str]:
    """
    Dynamically detects matching target parameter name from question keywords.
    Uses dynamic parameter vocabulary map loaded from configuration.
    """
    if explicit_param and isinstance(explicit_param, str) and explicit_param.strip():
        return explicit_param.strip()

    q_lower = (question or "").lower().strip()
    if not q_lower:
        return None

    vocab = vocabulary_map or load_intent_config().get("parameter_vocabulary_map", {})

    for param_name, keywords in vocab.items():
        for kw in keywords:
            kw_clean = kw.lower().strip()
            # Match multi-word phrase or single keyword word boundary
            if len(kw_clean.split()) > 1:
                if kw_clean in q_lower:
                    return param_name
            else:
                if re.search(r'\b' + re.escape(kw_clean) + r'\b', q_lower):
                    return param_name

    return None
