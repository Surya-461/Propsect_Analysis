import urllib.request
import urllib.parse
import urllib.error
import json
import time
import threading
from models.evidence import Evidence
import datetime

# Thread-safe in-memory cache for Wikipedia company lookups
_wiki_cache: dict[str, dict] = {}
_wiki_lock = threading.Lock()

# Wikimedia compliant User-Agent
WIKIPEDIA_USER_AGENT = "ProspectIQResearchBot/3.0 (https://prospect-iq.internal; research@prospect-iq.internal) python-urllib/3.12"

def fetch_wikipedia_profile(company_name: str) -> dict | None:
    """
    Fetches Wikipedia page summary for a company once, using caching,
    compliant User-Agent, and Retry-After / exponential backoff handling.
    """
    key = company_name.strip().lower()
    with _wiki_lock:
        if key in _wiki_cache:
            return _wiki_cache[key]

    wiki_query = urllib.parse.quote(f"{company_name} insurance company")
    wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={wiki_query}&format=json&utf8=1"

    req = urllib.request.Request(
        wiki_url,
        headers={
            "User-Agent": WIKIPEDIA_USER_AGENT,
            "Accept": "application/json"
        }
    )

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                search_items = data.get("query", {}).get("search", [])
                if search_items:
                    top_item = search_items[0]
                    clean_snippet = top_item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
                    wiki_title = top_item.get("title", "")
                    wiki_url_link = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(wiki_title)}"
                    
                    profile_data = {
                        "title": wiki_title,
                        "snippet": clean_snippet,
                        "url": wiki_url_link
                    }
                    with _wiki_lock:
                        _wiki_cache[key] = profile_data
                    return profile_data
            break
        except urllib.error.HTTPError as err:
            if err.code == 429:
                retry_after = err.headers.get("Retry-After")
                wait_sec = min(int(retry_after), 5) if retry_after and retry_after.isdigit() else (attempt + 1) * 2
                time.sleep(wait_sec)
            else:
                break
        except Exception:
            break

    return None

def collect_wikipedia_evidence(company_name: str, parameter: str) -> list[Evidence]:
    """
    Collects cached Wikipedia evidence for a given parameter without redundant HTTP calls.
    Returns empty list if Wikipedia result title does not match company_name.
    """
    profile = fetch_wikipedia_profile(company_name)
    if not profile:
        return []

    c_name = company_name.lower().strip()
    raw_tokens = [t for t in c_name.split() if len(t) >= 3]
    searchable = f"{profile['title']} {profile['snippet']}".lower()

    if raw_tokens and not any(tok in searchable for tok in raw_tokens):
        return []

    return [
        Evidence(
            parameter=parameter,
            title=f"{company_name} Corporate Profile: {profile['title']}",
            content=profile["snippet"],
            source_url=profile["url"],
            source_name="Wikipedia Knowledge Reference",
            source_type="company_website",
            retrieved_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            relevance=0.95
        )
    ]
