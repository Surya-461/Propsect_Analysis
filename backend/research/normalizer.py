import urllib.parse
from typing import List, Dict
from models.evidence import Evidence


TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "ref", "source", "ref_src", "ved", "usg", "session_id",
    "_hsenc", "_hsmi", "mc_cid", "mc_eid"
}


def normalize_url(raw_url: str) -> str:
    """
    Normalizes a URL to identify duplicate web sources across different search engines.
    - Standardizes scheme (http/https) and lowercases domain name.
    - Strips query tracking parameters (utm_*, ref, gclid, etc.).
    - Removes URL fragments/anchors and trailing slashes.
    """
    if not raw_url or not isinstance(raw_url, str):
        return ""

    url_str = raw_url.strip()
    try:
        parsed = urllib.parse.urlparse(url_str)
        if not parsed.netloc:
            return url_str

        scheme = (parsed.scheme or "https").lower()
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Clean query parameters
        clean_query = ""
        if parsed.query:
            query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
            filtered = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
            if filtered:
                clean_query = urllib.parse.urlencode(filtered)

        # Normalize path
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

        normalized = urllib.parse.urlunparse((
            scheme,
            netloc,
            path,
            "",
            clean_query,
            ""  # discard fragment
        ))
        return normalized
    except Exception:
        return url_str


def extract_domain(url: str) -> str:
    """Extracts clean domain name from URL."""
    if not url:
        return "web_source"
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc or "web_source"
    except Exception:
        return "web_source"


def deduplicate_evidence(evidence_list: List[Evidence]) -> List[Evidence]:
    """
    Deduplicates evidence collected across multiple providers (Tavily, Serper, RSS).
    Treats multiple search engines returning the same underlying URL as ONE source.
    Merges provider discovery tracking (discovered_by) and preserves maximum rich content.
    """
    deduped_map: Dict[str, Evidence] = {}

    for ev in evidence_list:
        if not ev.source_url:
            continue

        norm_url = normalize_url(ev.source_url)
        if not norm_url:
            continue

        domain = extract_domain(norm_url)
        ev.source_domain = domain
        provider = ev.provider or "search_provider"

        if norm_url not in deduped_map:
            if not ev.discovered_by:
                ev.discovered_by = [provider]
            elif provider not in ev.discovered_by:
                ev.discovered_by.append(provider)
            deduped_map[norm_url] = ev
        else:
            existing = deduped_map[norm_url]
            # Track cross-engine discovery without inflating independent evidence
            if provider and provider not in existing.discovered_by:
                existing.discovered_by.append(provider)
            
            # Prefer richer / longer text content or higher quality title
            if len(ev.content or "") > len(existing.content or ""):
                existing.content = ev.content
            if (not existing.published_date) and ev.published_date:
                existing.published_date = ev.published_date
            if (not existing.raw_extracted_content) and ev.raw_extracted_content:
                existing.raw_extracted_content = ev.raw_extracted_content
                existing.crawled_with_firecrawl = True

    return list(deduped_map.values())
