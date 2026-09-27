import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from models.evidence import Evidence
import datetime

def collect_google_news_evidence(query: str, parameter: str) -> list[Evidence]:
    """Collects evidence from Google News RSS feed."""
    evidence_items = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:3]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else None
                if title and link:
                    source_name = "Google News"
                    if "-" in title:
                        source_name = title.split("-")[-1].strip()
                    evidence_items.append(
                        Evidence(
                            parameter=parameter,
                            title=title,
                            content=title,
                            source_url=link,
                            source_name=source_name,
                            source_type="reputable_news",
                            published_date=pub_date,
                            retrieved_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            relevance=0.9
                        )
                    )
    except Exception as e:
        print(f"Collector Error (Google News): {e}")
    return evidence_items
