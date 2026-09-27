import os
import json
import urllib.request
import logging
from dotenv import load_dotenv
from models.evidence import Evidence
from research.collectors.free_content_extractor import extract_optional_deep_content

load_dotenv()
logger = logging.getLogger(__name__)

WEBCRAWLER_API_KEY = os.getenv("WEBCRAWLER_API_KEY", os.getenv("FIRECRAWL_API_KEY", "")).strip()


def extract_webcrawler_content(url: str, timeout: int = 15) -> dict | None:
    """
    Extracts structured page content and markdown using WebCrawlerAPI Scrape API v2.
    Endpoint: https://api.webcrawlerapi.com/v2/scrape
    """
    api_key = os.getenv("WEBCRAWLER_API_KEY", os.getenv("FIRECRAWL_API_KEY", WEBCRAWLER_API_KEY)).strip()
    if not api_key:
        logger.info("WEBCRAWLER_API_KEY not configured in .env. Skipping WebCrawlerAPI deep crawl.")
        return None

    if not url or not url.startswith(("http://", "https://")):
        return None

    # Don't try scraping search engine result pages or search queries directly
    if any(blocked in url.lower() for blocked in ["google.com/search", "bing.com/search", "search.yahoo"]):
        return None

    try:
        payload = {
            "url": url,
            "output_formats": ["markdown"],
            "main_content_only": True
        }

        req = urllib.request.Request(
            "https://api.webcrawlerapi.com/v2/scrape",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ProspectAI-Intelligence/3.1 (WebCrawler Extractor)"
            }
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                res_data = json.loads(resp.read().decode("utf-8"))
                markdown_content = ""
                title = ""
                metadata = {}

                if isinstance(res_data, dict):
                    # Direct v2 format: { "success": true, "markdown": "...", "page_title": "..." }
                    markdown_content = res_data.get("markdown", "")
                    if not markdown_content and "data" in res_data and isinstance(res_data["data"], dict):
                        # Nested format fallback
                        markdown_content = res_data["data"].get("markdown", "") or res_data["data"].get("content", "")
                        metadata = res_data["data"].get("metadata", {})
                        title = metadata.get("title") or metadata.get("ogTitle") or ""

                    if not title:
                        title = res_data.get("page_title") or res_data.get("title") or ""

                    if markdown_content and len(markdown_content.strip()) > 50:
                        return {
                            "markdown": markdown_content.strip(),
                            "title": title,
                            "metadata": metadata or {"page_title": title, "status": res_data.get("status")},
                            "url": url
                        }
    except urllib.error.HTTPError as e:
        if getattr(e, "code", None) in (402, 403, 429):
            logger.warning(
                "WebCrawlerAPI deep crawl skipped for '%s' (HTTP %s: payment required / quota exceeded). "
                "Attempting free trafilatura fallback.",
                url,
                e.code,
            )
            return extract_optional_deep_content(url, timeout=timeout)
        logger.info("WebCrawlerAPI scrape notice for URL '%s': %s", url, e)
    except Exception as e:
        logger.info("WebCrawlerAPI scrape notice for URL '%s': %s", url, e)

    return extract_optional_deep_content(url, timeout=timeout)


import re

def _clean_crawled_markdown(md_text: str) -> str:
    """
    Strips navigation boilerplate, cookie banners, currency dropdown lists,
    and PDF TOC number chains from crawled markdown before evidence ingestion.
    """
    if not md_text:
        return ""
    lines = md_text.splitlines()
    clean_lines = []
    for line in lines:
        l_str = line.strip()
        if not l_str:
            continue
        # Skip lines that are just currency selectors or nav links
        if re.search(r'\$\s*USD\b.*?(?:EUR|INR|GBP|CAD|AUD)', l_str, re.IGNORECASE):
            continue
        if re.search(r'\b(Sign In|Log In|English|Deutsch|Français|Propose a change)\b', l_str, re.IGNORECASE) and len(l_str) < 120:
            continue
        # Skip raw PDF TOC chains like 94-247 248-460 461-470
        if re.search(r'(\b\d+-\d+\b\s*){2,}', l_str):
            continue
        # Skip raw number streams
        if re.search(r'(\b\d+[\d,.]*\b\s*){5,}', l_str):
            continue
        clean_lines.append(l_str)
    return "\n".join(clean_lines)


def enrich_evidence_with_crawler(
    evidence_list: list[Evidence],
    max_crawl: int = 3,
    min_authority_tier: int = 3
) -> list[Evidence]:
    """
    Enriches top-ranked authoritative evidence items with full page content via WebCrawlerAPI.
    Targets Tier 1-3 sources (regulatory, annual reports, investor relations, reputable news).
    Preserves original high-yield search snippets and rejects boilerplate/PDF TOC overwrites.
    """
    crawled_count = 0
    for ev in evidence_list:
        if crawled_count >= max_crawl:
            break

        # Only crawl if authority tier is high enough and content is currently short snippet
        if ev.authority_tier <= min_authority_tier and (not ev.crawled_with_firecrawl):
            url_str = ev.source_url or ""
            url_lower = url_str.lower()
            if not url_str.startswith("http"):
                continue
            if any(k in url_lower for k in ["google.com/search", "wikipedia.org", "yahoo.com", "bing.com"]):
                continue
            # Do NOT scrape raw PDF files with markdown extractor: search engine snippets
            # already contain the specific matched page content; raw PDF scraping yields TOCs
            if url_lower.endswith(".pdf") or ".pdf?" in url_lower or "/pdf/" in url_lower:
                continue

            scrape_res = extract_webcrawler_content(ev.source_url)
            if scrape_res and scrape_res.get("markdown"):
                md_text = scrape_res["markdown"]
                cleaned_md = _clean_crawled_markdown(md_text)
                ev.raw_extracted_content = md_text

                # If crawled content is substantive, enrich without losing original snippet
                orig_snippet = (ev.content or "").strip()
                if cleaned_md and len(cleaned_md) >= 60:
                    if orig_snippet and orig_snippet not in cleaned_md:
                        ev.content = f"{orig_snippet}\n\n{cleaned_md[:1500]}".strip()
                    else:
                        ev.content = cleaned_md[:2000]
                elif orig_snippet:
                    # Keep original search snippet if crawled text was mostly boilerplate
                    ev.content = orig_snippet

                if scrape_res.get("title") and (not ev.title or "Insight" in ev.title):
                    ev.title = scrape_res["title"]
                ev.crawled_with_firecrawl = True
                crawled_count += 1

    return evidence_list


# Backward compatibility aliases
extract_firecrawl_content = extract_webcrawler_content
enrich_evidence_with_firecrawl = enrich_evidence_with_crawler

