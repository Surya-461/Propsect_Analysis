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

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "").strip()


def collect_serper_evidence(
    query: str,
    parameter: str,
    max_results: int = 5,
    prospect_name: str = "",
    metric: str = "",
    query_type: str = ""
) -> list[Evidence]:
    """
    Collects web research evidence using Serper.dev Google Search API.
    Extracts URLs, snippets, titles, publication dates, and source domains.
    """
    evidence_items: list[Evidence] = []
    api_key = os.getenv("SERPER_API_KEY", SERPER_API_KEY).strip()

    if not api_key:
        logger.warning("SERPER_API_KEY not configured in .env. Skipping Serper collector.")
        return evidence_items

    # Safe diagnostic logging (no API keys exposed)
    logger.info(
        f"[RESEARCH QUERY]\n"
        f"Prospect: {prospect_name or 'N/A'}\n"
        f"Parameter: {parameter}\n"
        f"Metric: {metric or 'N/A'}\n"
        f"Provider: Serper\n"
        f"Query: {query}"
    )

    try:
        payload = {
            "q": query,
            "num": max_results,
            "gl": "in",  # Global / Indian market context
            "hl": "en"
        }

        req = urllib.request.Request(
            "https://google.serper.dev/search",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
                "User-Agent": "ProspectAI-Intelligence/3.1"
            }
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                res_data = json.loads(resp.read().decode("utf-8"))
                organic_results = res_data.get("organic", [])

                logger.info(
                    f"[SEARCH RESULT]\n"
                    f"Provider: Serper\n"
                    f"Results: {len(organic_results)}"
                )

                for item in organic_results:
                    title = item.get("title", "").strip()
                    url = item.get("link", "").strip()
                    snippet = item.get("snippet", "").strip()
                    date_str = item.get("date")

                    if url and (title or snippet):
                        parsed_url = urllib.parse.urlparse(url)
                        domain = parsed_url.netloc.replace("www.", "").lower() if parsed_url.netloc else "serper.dev"

                        evidence_items.append(
                            Evidence(
                                parameter=parameter,
                                metric=metric or None,
                                query_type=query_type or "serper_search",
                                search_query=query,
                                title=title or f"{parameter} Insight",
                                content=snippet or title,
                                source_url=url,
                                source_name=domain or "Serper Search Result",
                                source_domain=domain,
                                source_type="serper_search",
                                provider="serper",
                                published_date=date_str,
                                retrieved_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                relevance=0.90,
                                discovered_by=["serper"]
                            )
                        )

                # Also harvest top sitelinks or knowledge graph if present
                knowledge_graph = res_data.get("knowledgeGraph")
                if knowledge_graph and isinstance(knowledge_graph, dict):
                    kg_title = knowledge_graph.get("title", "")
                    kg_desc = knowledge_graph.get("description", "")
                    kg_url = knowledge_graph.get("website", "") or knowledge_graph.get("descriptionLink", "")
                    if kg_desc and kg_url:
                        kg_domain = urllib.parse.urlparse(kg_url).netloc.replace("www.", "").lower()
                        evidence_items.append(
                            Evidence(
                                parameter=parameter,
                                metric=metric or "Knowledge Graph",
                                query_type="official_profile",
                                search_query=query,
                                title=f"{kg_title} Official Overview",
                                content=kg_desc,
                                source_url=kg_url,
                                source_name=kg_domain or "Knowledge Graph",
                                source_domain=kg_domain,
                                source_type="official_profile",
                                provider="serper",
                                retrieved_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                relevance=0.95,
                                discovered_by=["serper"]
                            )
                        )
    except Exception as e:
        logger.warning(f"Collector Error (Serper Search for '{query}'): {e}")

    return evidence_items
