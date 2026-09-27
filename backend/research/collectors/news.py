import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from models.evidence import Evidence
import datetime

def collect_industry_news_evidence(company_name: str, parameter: str) -> list[Evidence]:
    """Collects industry news evidence for insurance & business trends."""
    evidence_items = []
    try:
        query = f"{company_name} insurance industry market growth partnership"
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            xml_data = resp.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:2]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else None
                if title and link:
                    evidence_items.append(
                        Evidence(
                            parameter=parameter,
                            title=title,
                            content=f"Industry news context: {title}",
                            source_url=link,
                            source_name="Insurance Industry Press",
                            source_type="reputable_news",
                            published_date=pub_date.strip() if pub_date else None,
                            retrieved_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            relevance=0.85
                        )
                    )
    except Exception as e:
        print(f"Collector Error (News): {e}")
    return evidence_items
