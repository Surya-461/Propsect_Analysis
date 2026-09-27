import logging

try:
    import trafilatura
except ImportError:  # pragma: no cover - optional dependency fallback
    trafilatura = None

logger = logging.getLogger(__name__)


def extract_trafilatura_content(url: str, timeout: int = 15) -> dict | None:
    """Free fallback extractor for public web pages.

    This is used when Firecrawl is unavailable, quota-blocked, or not configured.
    """
    if not url or not url.startswith(("http://", "https://")):
        return None
    if trafilatura is None:
        logger.info("trafilatura is not installed; skipping free deep-content extraction for '%s'.", url)
        return None

    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None

        extracted = trafilatura.extract(
            downloaded,
            include_formatting=False,
            include_links=False,
            output_format="txt",
            favor_precision=True,
        )
        if not extracted or len(extracted.strip()) < 80:
            return None

        metadata = trafilatura.extract_metadata(downloaded) or {}
        title = getattr(metadata, "title", None) or ""
        return {
            "markdown": extracted.strip()[:5000],
            "title": title,
            "metadata": {"title": title},
            "url": url,
        }
    except Exception as exc:
        logger.info("trafilatura extraction notice for URL '%s': %s", url, exc)
        return None


def extract_optional_deep_content(url: str, timeout: int = 15, firecrawl_lambda=None) -> dict | None:
    """Run the best available content extractor without breaking the research flow."""
    if not url or not url.startswith(("http://", "https://")):
        return None

    if firecrawl_lambda is not None:
        try:
            result = firecrawl_lambda(url, timeout=timeout)
            if result:
                return result
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.info("Primary extractor failed for '%s': %s", url, exc)

    return extract_trafilatura_content(url, timeout=timeout)
