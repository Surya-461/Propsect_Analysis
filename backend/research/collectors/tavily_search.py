import os
import json
import urllib.request
import urllib.parse
import datetime
import logging
from dotenv import load_dotenv
from models.evidence import Evidence

load_dotenv()
logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()

def collect_tavily_evidence(
    query: str,
    parameter: str,
    max_results: int = 3,
    include_domains: list[str] | None = None,
    prospect_name: str = "",
    metric: str = "",
    query_type: str = ""
) -> list[Evidence]:
    """
    Collects rich web research evidence using Tavily Search API.
    Extracts URLs, full context snippets, titles, and sources.
    Passes domain restrictions natively via include_domains.
    """
    evidence_items: list[Evidence] = []
    api_key = os.getenv("TAVILY_API_KEY", TAVILY_API_KEY).strip()

    if not api_key:
        logger.warning("TAVILY_API_KEY not configured in .env. Falling back to alternative collectors.")
        return evidence_items

    # Safe diagnostic logging (no API keys exposed)
    logger.info(
        f"[RESEARCH QUERY]\n"
        f"Prospect: {prospect_name or 'N/A'}\n"
        f"Parameter: {parameter}\n"
        f"Metric: {metric or 'N/A'}\n"
        f"Provider: Tavily\n"
        f"Query: {query}"
    )

    try:
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "max_results": max_results
        }
        if include_domains and isinstance(include_domains, list):
            clean_domains = [d.strip().replace("http://", "").replace("https://", "").replace("www.", "") for d in include_domains if d.strip()]
            if clean_domains:
                payload["include_domains"] = clean_domains

        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ProspectAI-Intelligence/3.0"
            }
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                res_data = json.loads(resp.read().decode("utf-8"))
                results = res_data.get("results", [])

                logger.info(
                    f"[SEARCH RESULT]\n"
                    f"Provider: Tavily\n"
                    f"Results: {len(results)}"
                )

                for r in results:
                    title = r.get("title", "").strip()
                    url = r.get("url", "").strip()
                    content = r.get("content", "").strip()
                    score = float(r.get("score", 0.95))

                    if url and (title or content):
                        # Extract domain name as source name
                        parsed_url = urllib.parse.urlparse(url)
                        domain_name = parsed_url.netloc.replace("www.", "").lower() if parsed_url.netloc else "Web Source"
                        pub_date = r.get("published_date") or r.get("date") or None

                        evidence_items.append(
                            Evidence(
                                parameter=parameter,
                                metric=metric or None,
                                query_type=query_type or "tavily_search",
                                search_query=query,
                                title=title or f"{parameter} Insight",
                                content=content or title,
                                source_url=url,
                                source_name=domain_name,
                                source_domain=domain_name,
                                source_type="tavily_search",
                                provider="tavily",
                                published_date=str(pub_date).strip() if pub_date else None,
                                retrieved_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                relevance=min(1.0, max(0.6, score)),
                                discovered_by=["tavily"]
                            )
                        )
    except Exception as e:
        logger.warning(f"Collector Error (Tavily Search for '{query}'): {e}")

    return evidence_items
