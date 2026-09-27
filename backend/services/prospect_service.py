"""
Authoritative Insurance Prospect Service & Repository.
Loads, normalizes, searches, and resolves prospects from backend/data/insurance_prospects_250.json.
This is the single source of truth for the supported insurance prospect universe.
"""

import os
import json
import re
import logging
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
PROSPECTS_JSON_PATH = os.path.join(DATA_DIR, "insurance_prospects_250.json")

# In-memory cache with file modification timestamp tracking
_PROSPECTS_CACHE: List[Dict[str, str]] = []
_LAST_MTIME: float = 0.0

# Curated alias and abbreviation mappings pointing to exact names in insurance_prospects_250.json
KNOWN_ALIASES: Dict[str, str] = {
    # Indian Life & General Insurers
    "sbi life": "SBI Life Insurance",
    "sbi life insurance": "SBI Life Insurance",
    "sbi general": "SBI General Insurance",
    "sbi general insurance": "SBI General Insurance",
    "sbi insurance": "SBI Insurance",
    "hdfc life": "HDFC Life",
    "hdfc life insurance": "HDFC Life",
    "hdfc ergo": "HDFC ERGO",
    "hdfc ergo general insurance": "HDFC ERGO",
    "icici lombard": "ICICI Lombard",
    "icici lombard general insurance": "ICICI Lombard",
    "icici prudential": "ICICI Prudential Life Insurance",
    "icici pru": "ICICI Prudential Life Insurance",
    "icici pru life": "ICICI Prudential Life Insurance",
    "icici prudential life": "ICICI Prudential Life Insurance",
    "lic": "Life Insurance Corporation of India",
    "life insurance corporation": "Life Insurance Corporation of India",
    "life insurance corporation of india": "Life Insurance Corporation of India",
    "tata aia": "Tata AIA Life Insurance",
    "tata aia life": "Tata AIA Life Insurance",
    "tata aig": "Tata AIG General Insurance",
    "tata aig general": "Tata AIG General Insurance",
    "bajaj allianz life": "Bajaj Allianz Life Insurance",
    "bajaj allianz general": "Bajaj Allianz General Insurance",
    "star health": "Star Health and Allied Insurance",
    "star health insurance": "Star Health and Allied Insurance",
    "star health and allied": "Star Health and Allied Insurance",
    "star union": "Star Union Dai-ichi Life Insurance",
    "star union dai-ichi": "Star Union Dai-ichi Life Insurance",
    "sud life": "Star Union Dai-ichi Life Insurance",
    "max life": "Max Life Insurance",
    "kotak life": "Kotak Mahindra Life Insurance",
    "kotak mahindra life": "Kotak Mahindra Life Insurance",
    "aditya birla sun life": "Aditya Birla Sun Life Insurance",
    "absli": "Aditya Birla Sun Life Insurance",
    "aditya birla health": "Aditya Birla Health Insurance",
    "care health": "Care Health Insurance",
    "niva bupa": "Niva Bupa Health Insurance",
    "max bupa": "Niva Bupa Health Insurance",
    "new india assurance": "New India Assurance",
    "the new india assurance": "New India Assurance",
    "united india": "United India Insurance",
    "united india insurance": "United India Insurance",
    "oriental insurance": "Oriental Insurance",
    "the oriental insurance": "Oriental Insurance",
    "national insurance": "National Insurance Company",
    "national insurance company": "National Insurance Company",
    "gic re": "General Insurance Corporation of India",
    "general insurance corporation": "General Insurance Corporation of India",
    "pnb metlife": "PNB MetLife India Insurance",
    "indiafirst": "IndiaFirst Life Insurance",
    "canara hsbc": "Canara HSBC Life Insurance",
    "ageas federal": "Ageas Federal Life Insurance",
    "edelweiss life": "Edelweiss Life Insurance",
    "shriram life": "Shriram Life Insurance",
    "reliance nippon": "Reliance Nippon Life Insurance",
    "aviva india": "Aviva Life Insurance India",
    "future generali": "Future Generali India Insurance",
    "future generali life": "Future Generali India Life Insurance",
    "axis max life": "Axis Max Life Insurance",
    "reliance general": "Reliance General Insurance",
    "go digit": "Go Digit General Insurance",
    "digit": "Go Digit General Insurance",
    "acko": "ACKO General Insurance",
    "iffco tokio": "IFFCO Tokio General Insurance",
    "chola ms": "Chola MS General Insurance",
    "royal sundaram": "Royal Sundaram General Insurance",
    "universal sompo": "Universal Sompo General Insurance",
    "liberty general": "Liberty General Insurance",
    "magma hdi": "Magma HDI General Insurance",
    "navi": "Navi General Insurance",
    "kotak general": "Kotak General Insurance",
    "zuno": "Zuno General Insurance",
    "manipalcigna": "ManipalCigna Health Insurance",
    "galaxy health": "Galaxy Health Insurance",

    # Global Life, P&C, Reinsurance & Health Carriers
    "allianz": "Allianz",
    "axa": "AXA",
    "zurich": "Zurich Insurance Group",
    "zurich insurance": "Zurich Insurance Group",
    "zurich group": "Zurich Insurance Group",
    "aig": "AIG",
    "american international group": "AIG",
    "metlife": "MetLife",
    "prudential plc": "Prudential plc",
    "prudential financial": "Prudential Financial",
    "chubb": "Chubb",
    "chubb limited": "Chubb",
    "generali": "Generali",
    "munich re": "Munich Re",
    "munich reinsurance": "Munich Re",
    "swiss re": "Swiss Re",
    "swiss reinsurance": "Swiss Re",
    "hannover re": "Hannover Re",
    "scor": "SCOR",
    "berkshire": "Berkshire Hathaway",
    "berkshire hathaway": "Berkshire Hathaway",
    "manulife": "Manulife",
    "sun life": "Sun Life Financial",
    "sun life financial": "Sun Life Financial",
    "aia": "AIA Group",
    "aia group": "AIA Group",
    "ping an": "Ping An Insurance",
    "ping an insurance": "Ping An Insurance",
    "china life": "China Life Insurance",
    "china pacific": "China Pacific Insurance",
    "cpic": "China Pacific Insurance",
    "tokio marine": "Tokio Marine",
    "sompo": "Sompo Holdings",
    "sompo holdings": "Sompo Holdings",
    "ms&ad": "MS&AD Insurance Group",
    "dai-ichi life": "Dai-ichi Life Holdings",
    "nippon life": "Nippon Life",
    "meiji yasuda": "Meiji Yasuda Life",
    "t&d": "T&D Holdings",
    "fwd": "FWD Group",
    "qbe": "QBE Insurance Group",
    "suncorp": "Suncorp Group",
    "iag": "Insurance Australia Group",
    "insurance australia": "Insurance Australia Group",
    "medibank": "Medibank",
    "asr nederland": "ASR Nederland",
    "asr": "ASR Nederland",
    "nn group": "NN Group",
    "aegon": "Aegon",
    "ageas": "Ageas",
    "aviva": "Aviva",
    "legal & general": "Legal & General",
    "legal and general": "Legal & General",
    "l&g": "Legal & General",
    "m&g": "M&G",
    "phoenix group": "Phoenix Group",
    "hiscox": "Hiscox",
    "admiral": "Admiral Group",
    "direct line": "Direct Line Group",
    "beazley": "Beazley",
    "lancashire": "Lancashire Holdings",
    "mapfre": "MAPFRE",
    "cnp": "CNP Assurances",
    "bnp paribas cardif": "BNP Paribas Cardif",
    "cardif": "BNP Paribas Cardif",
    "credit agricole": "Crédit Agricole Assurances",
    "groupama": "Groupama",
    "covea": "COVEA",
    "talanx": "Talanx",
    "hdi": "HDI",
    "vienna insurance": "Vienna Insurance Group",
    "vig": "Vienna Insurance Group",
    "ergo": "ERGO Group",
    "baloise": "Baloise",
    "helvetia": "Helvetia",
    "swiss life": "Swiss Life",
    "unipol": "Unipol",
    "sampo": "Sampo",
    "tryg": "Tryg",
    "gjensidige": "Gjensidige",
    "storebrand": "Storebrand",
    "state farm": "State Farm",
    "geico": "GEICO",
    "progressive": "Progressive",
    "allstate": "Allstate",
    "liberty mutual": "Liberty Mutual",
    "travelers": "Travelers",
    "the travelers": "Travelers",
    "usaa": "USAA",
    "nationwide": "Nationwide",
    "farmers": "Farmers Insurance",
    "american family": "American Family Insurance",
    "erie": "Erie Insurance",
    "the hartford": "The Hartford",
    "hartford": "The Hartford",
    "cincinnati financial": "Cincinnati Financial",
    "aflac": "Aflac",
    "principal financial": "Principal Financial Group",
    "northwestern mutual": "Northwestern Mutual",
    "new york life": "New York Life",
    "massmutual": "MassMutual",
    "guardian life": "Guardian Life",
    "lincoln financial": "Lincoln Financial",
    "equitable": "Equitable Holdings",
    "unum": "Unum",
    "centene": "Centene",
    "cigna": "Cigna",
    "humana": "Humana",
    "elevance health": "Elevance Health",
    "elevance": "Elevance Health",
    "unitedhealth": "UnitedHealth Group",
    "unitedhealth group": "UnitedHealth Group",
    "kaiser permanente": "Kaiser Permanente",
    "kaiser": "Kaiser Permanente",
    "blue cross": "Blue Cross Blue Shield",
    "bcbs": "Blue Cross Blue Shield",
    "oscar health": "Oscar Health",
    "molina": "Molina Healthcare",
    "globe life": "Globe Life",
    "voya": "Voya Financial",
    "markel": "Markel Group",
    "wr berkley": "W. R. Berkley",
    "w. r. berkley": "W. R. Berkley",
    "arch capital": "Arch Capital Group",
    "picc": "PICC",
    "peoples insurance company of china": "People's Insurance Company of China",
    "china taiping": "China Taiping Insurance",
    "china reinsurance": "China Reinsurance",
    "taikang": "Taikang Insurance Group",
    "taikang life": "Taikang Life",
    "taiping life": "Taiping Life",
    "sumitomo life": "Sumitomo Life Insurance",
    "sony life": "Sony Life Insurance",
    "japan post": "Japan Post Insurance",
    "asahi life": "Asahi Life Insurance",
    "rakuten life": "Rakuten Life Insurance",
    "samsung life": "Samsung Life Insurance",
    "samsung fire": "Samsung Fire & Marine Insurance",
    "hanwha life": "Hanwha Life Insurance",
    "db insurance": "DB Insurance",
    "hyundai marine": "Hyundai Marine & Fire Insurance",
    "kb insurance": "KB Insurance",
    "kyobo life": "Kyobo Life Insurance",
    "great eastern": "Great Eastern",
    "tawuniya": "Tawuniya",
    "bupa arabia": "Bupa Arabia",
    "sanlam": "Sanlam",
    "old mutual": "Old Mutual",
    "discovery": "Discovery",
    "momentum metropolitan": "Momentum Metropolitan",
    "santam": "Santam",
    "hollard": "Hollard",
    "outsurance": "OUTsurance",
    "liberty group": "Liberty Group"
}

# Generic corporate stopwords ignored when token scoring against candidate names
STOPWORDS = {
    "insurance", "assurance", "reinsurance", "re", "group", "holdings", "holding",
    "corporation", "corp", "limited", "ltd", "company", "co", "inc", "incorporated",
    "plc", "the", "and", "&", "se", "sa", "ag", "nv", "pvt", "private", "public",
    "mutual", "international", "global", "general", "life", "financial", "services"
}


def load_prospects(force_reload: bool = False) -> List[Dict[str, str]]:
    """
    Dynamically loads insurance prospects from backend/data/insurance_prospects_250.json.
    Automatically invalidates cache if the file on disk changes.
    """
    global _PROSPECTS_CACHE, _LAST_MTIME

    current_mtime = 0.0
    if os.path.exists(PROSPECTS_JSON_PATH):
        try:
            current_mtime = os.path.getmtime(PROSPECTS_JSON_PATH)
        except OSError:
            current_mtime = 0.0

    if not force_reload and _PROSPECTS_CACHE and current_mtime == _LAST_MTIME and current_mtime > 0:
        return _PROSPECTS_CACHE

    prospects = []
    if os.path.exists(PROSPECTS_JSON_PATH):
        try:
            with open(PROSPECTS_JSON_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    prospects = [
                        {"id": str(item.get("id", "")).strip(), "name": str(item.get("name", "")).strip()}
                        for item in loaded
                        if isinstance(item, dict) and item.get("name")
                    ]
        except Exception as e:
            logger.error("Error loading prospects from %s: %s", PROSPECTS_JSON_PATH, e)

    _PROSPECTS_CACHE = prospects
    _LAST_MTIME = current_mtime
    logger.info("Loaded %d prospects from %s", len(prospects), PROSPECTS_JSON_PATH)
    return _PROSPECTS_CACHE


def get_all_prospects() -> List[Dict[str, str]]:
    """Returns the full list of canonical insurance prospects."""
    return load_prospects()


def clean_query_text(text: str) -> str:
    """Strips conversational prefixes, quotes, and punctuation."""
    if not text:
        return ""
    cleaned = str(text).strip()
    # Strip leading command verbs
    cleaned = re.sub(
        r'^(?:analyze|search(?:\s+for)?|look\s+up|find|report(?:\s+on)?|show\s+me|tell\s+me\s+about|evaluate|dossier\s+for|what\s+is\s+the\s+financial\s+strength\s+of|what\s+about)\s+(?:the\s+)?(?:prospect\s+|company\s+)?',
        '',
        cleaned,
        flags=re.IGNORECASE
    ).strip()
    # Match inside quotes if user quoted the company name
    match_quote = re.search(r"['\"]([^'\"]+)['\"]", cleaned)
    if match_quote and len(match_quote.group(1).strip()) > 1:
        return match_quote.group(1).strip()
    # Strip trailing punctuation
    cleaned = re.sub(r'[\?\.\,\!\:\;]+$', '', cleaned).strip()
    return cleaned


def normalize_company_name(text: str) -> str:
    """
    Normalizes a company name by lowercasing, replacing ampersands,
    removing punctuation, and stripping corporate suffixes.
    """
    cleaned = clean_query_text(text).lower()
    cleaned = cleaned.replace("&", "and")
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', cleaned)
    words = cleaned.split()
    filtered = [w for w in words if w not in STOPWORDS]
    if filtered:
        return " ".join(filtered)
    return " ".join(words)


def extract_meaningful_tokens(text: str) -> List[str]:
    """Extracts distinctive tokens excluding generic corporate words."""
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', text.lower()).strip()
    words = cleaned.split()
    meaningful = [w for w in words if w not in STOPWORDS and len(w) >= 2]
    return meaningful if meaningful else words


def search_prospects(query: str, limit: int = 15) -> List[Dict[str, str]]:
    """
    Searches the insurance prospects list for matching candidates.
    Used by autocomplete endpoints and search suggestions.
    """
    prospects = load_prospects()
    if not query or not query.strip():
        return prospects[:limit]

    cleaned = clean_query_text(query).strip()
    q_lower = cleaned.lower()
    q_norm = normalize_company_name(cleaned)
    q_tokens = extract_meaningful_tokens(cleaned)

    scored_results = []
    for p in prospects:
        p_name = p["name"]
        p_lower = p_name.lower()
        p_norm = normalize_company_name(p_name)
        p_tokens = extract_meaningful_tokens(p_name)
        score = 0

        # Exact ID match
        if p.get("id", "").lower() == q_lower:
            score += 100

        # Exact name match
        if p_lower == q_lower:
            score += 90
        elif p_norm == q_norm and q_norm:
            score += 80
        elif p_lower.startswith(q_lower):
            score += 70
        elif q_lower in p_lower:
            score += 50
        elif p_norm and q_norm and (q_norm in p_norm or p_norm in q_norm):
            score += 40
        else:
            # Meaningful Token overlap score
            overlap = [
                t for t in q_tokens 
                if any(t == pt or (len(t) >= 3 and len(pt) >= 3 and (t.startswith(pt) or pt.startswith(t))) for pt in p_tokens)
            ]
            if overlap:
                score += len(overlap) * 20

        if score > 0:
            scored_results.append((score, p))

    # Sort descending by score, then alphabetically
    scored_results.sort(key=lambda x: (-x[0], x[1]["name"]))
    return [item[1] for item in scored_results[:limit]]


def resolve_prospect(query: str) -> Tuple[Optional[Dict[str, str]], List[Dict[str, str]], str]:
    """
    Resolves a user-entered prospect string to a canonical prospect record from the JSON universe.
    
    Matching steps:
    1. ID lookup (e.g. 'INS-0114')
    2. Exact case-insensitive match on name (e.g. 'SBI Life Insurance')
    3. Curated alias dictionary match (e.g. 'SBI Life' -> 'SBI Life Insurance')
    4. Normalized name match (e.g. 'sbi life' -> 'SBI Life Insurance')
    5. Token & Substring match:
       - Single match -> resolved!
       - Multiple matches -> returns candidate list for disambiguation.
       - No match -> returns NOT_FOUND with friendly message.
       
    Returns:
    (canonical_prospect_dict_or_None, candidate_list, status_string)
    """
    prospects = load_prospects()
    if not prospects:
        return None, [], "PROSPECTS_UNAVAILABLE"

    cleaned = clean_query_text(query).strip()
    if not cleaned:
        return None, [], "EMPTY_INPUT"

    q_lower = cleaned.lower()

    # Step 1: ID Match
    for p in prospects:
        if p.get("id", "").lower() == q_lower:
            return p, [p], "EXACT_MATCH"

    # Step 2: Exact Name Match
    for p in prospects:
        if p["name"].lower() == q_lower:
            return p, [p], "EXACT_MATCH"

    # Step 3: Curated Alias Match
    if q_lower in KNOWN_ALIASES:
        canonical_target = KNOWN_ALIASES[q_lower].lower()
        for p in prospects:
            if p["name"].lower() == canonical_target:
                return p, [p], "ALIAS_MATCH"

    # Step 4: Normalized Name Match
    q_norm = normalize_company_name(cleaned)
    if q_norm:
        norm_matches = [p for p in prospects if normalize_company_name(p["name"]) == q_norm]
        if len(norm_matches) == 1:
            return norm_matches[0], norm_matches, "NORMALIZED_MATCH"
        elif len(norm_matches) > 1:
            exact_prefix = [p for p in norm_matches if p["name"].lower().startswith(q_lower)]
            if len(exact_prefix) == 1:
                return exact_prefix[0], norm_matches, "NORMALIZED_MATCH"
            return None, norm_matches, "MULTIPLE_MATCHES"

    # Step 5: Meaningful Token & Substring matching
    matches = search_prospects(cleaned, limit=10)
    if not matches:
        return None, [], "NOT_FOUND"

    if len(matches) == 1:
        return matches[0], matches, "FUZZY_MATCH"

    # Check if query words strictly match a single prospect
    q_tokens = extract_meaningful_tokens(cleaned)
    strong_matches = [
        m for m in matches 
        if all(w in m["name"].lower() for w in q_tokens)
    ]
    if len(strong_matches) == 1:
        return strong_matches[0], matches, "STRONG_MATCH"

    # Check if query is an exact prefix for one match
    exact_prefix_matches = [m for m in matches if m["name"].lower().startswith(q_lower)]
    if len(exact_prefix_matches) == 1:
        return exact_prefix_matches[0], matches, "EXACT_MATCH"

    # Ambiguous - multiple possibilities (e.g. user typed "SBI" or "Prudential")
    return None, matches, "MULTIPLE_MATCHES"


def validate_prospects_catalog() -> Dict[str, Any]:
    """
    Validates that the 250 prospects universe contains exactly 250 unique prospects
    with unique canonical IDs INS-0001 to INS-0250 and unique names.
    """
    prospects = load_prospects()
    total_count = len(prospects)
    ids = [p.get("id", "").strip() for p in prospects if p.get("id")]
    names = [p.get("name", "").strip() for p in prospects if p.get("name")]

    unique_ids = set(ids)
    unique_names = set(names)

    expected_ids = {f"INS-{i:04d}" for i in range(1, 251)}
    actual_ids = set(ids)

    missing_from_expected = expected_ids - actual_ids
    unexpected_ids = actual_ids - expected_ids

    missing_ids = total_count - len(ids)
    missing_names = total_count - len(names)

    is_valid = (
        total_count == 250
        and len(unique_ids) == 250
        and len(unique_names) == 250
        and len(missing_from_expected) == 0
        and len(unexpected_ids) == 0
        and missing_ids == 0
        and missing_names == 0
    )

    return {
        "valid": is_valid,
        "total_count": total_count,
        "unique_ids_count": len(unique_ids),
        "unique_names_count": len(unique_names),
        "missing_ids": missing_ids,
        "missing_names": missing_names,
        "missing_from_expected": list(missing_from_expected),
        "unexpected_ids": list(unexpected_ids)
    }
