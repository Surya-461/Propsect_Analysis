# Prospect AI: Output Governance & Verification Specification

**Document Classification:** Authoritative Technical & Governance Specification  
**Version:** 2.0  
**Domain:** Commercial Insurance Underwriting & Prospect Intelligence  
**Scope:** Input Validation, Multi-Source Aggregation, Source Authority Hierarchy, Deduplication, Conflict Resolution, Citation Behavior, and Output Quality Rules.

---

## 1. Objective

The Prospect AI system analyzes a predefined set of insurance prospect companies using multiple research sources and produces parameter-specific underwriting intelligence.

The objective of these governance rules is to ensure that every generated analysis is:
* **Prospect-specific**: Grounded exclusively in the requested target prospect.
* **Parameter-specific**: Mapped strictly to the relevant underwriting parameter.
* **Evidence-backed**: Every factual observation is backed by empirical research disclosures.
* **Source-traceable**: Direct link and attribution to the primary publishing source.
* **Date-aware**: Explicit distinction between fiscal reporting periods (e.g., FY2024 vs. FY2025).
* **Conflict-aware**: Transparent detection and reporting of discrepancies without artificial averaging.
* **Duplicate-aware**: Deduplication of factual values while preserving multi-source citations.
* **Citation-aware**: Multiple high-quality citations attached to corroborated facts.
* **Transparent about uncertainty**: Explicit reporting of missing or ambiguous data.
* **Resistant to hallucinated facts**: Strict constraint against fabricated metrics, dates, or URLs.
* **Consistent across prospects & parameters**: Deterministic schema and quality standards.

The system prioritizes **accuracy and traceability over simply producing a populated response**.

---

## 2. Prospect Scope Constraint

Input validation is strictly bounded to the predefined prospect universe.

1. **Predefined Universe**: The supported prospect catalog contains approximately **250–300 predefined insurance companies** (`insurance_prospects_250.json`).
2. **Deterministic Resolution**: Incoming user queries resolve against canonical IDs, official legal names, and registered aliases.
3. **Rejection Policy**: If a prospect is not part of the supported registry, the system must **never silently perform unrestricted web crawling**. It must return:
   > *"This prospect is not currently supported. Please select a company from the supported prospect list."*
4. **No Runtime Additions**: Prospects are not dynamically invented or appended during runtime.

---

## 3. Prospect Identity & Anti-Contamination Rule

Every research request maintains a canonical prospect identity. Every harvested evidence item must preserve:
```json
{
  "prospect": "HDFC Life",
  "parameter": "Business Growth",
  "fact": "Actual factual statement...",
  "source": "Official Annual Report",
  "url": "https://...",
  "publication_date": "2025-06-15",
  "reporting_period": "FY2025"
}
```
**Anti-Contamination Directive**: Evidence from one carrier (e.g., *ICICI Prudential*, *Allianz*, *Zurich*, *SBI Life*) must **never** appear under another prospect (e.g., *HDFC Life*).

---

## 4. Parameter Isolation Rule

Each parameter must receive only evidence relevant to that parameter:
* **Financial Strength**: Solvency ratio, balance sheet capital, credit ratings, audited profits.
* **Business Growth**: YoY premium expansion, new business premium, quarterly revenue momentum.
* **Market Position**: Market share ranking, peer comparisons, regulatory market segment ranking.
* **Insurance Performance / Risk**: Combined ratio, claim settlement ratio, underwriting profitability, loss ratios.
* **Operational Scale**: Branch footprint, distribution channels, bancassurance partners, agent workforce.
* **Technology Activity / Digital Transformation**: Core modernization, AI underwriting, cloud migrations, digital portal metrics.
* **Strategic Activity / M&A**: Mergers, acquisitions, joint ventures, bancassurance alliances.

Evidence is mapped deterministically to avoid cross-parameter pollution.

---

## 5. Research Source & Provider Rules

The system integrates multiple research sources according to their distinct roles:
* **Search Providers (Discovery Engines)**: Tavily AI Search, Serper.dev Google Search API, Google News RSS, Financial News RSS, Industry Press RSS, Wikipedia Knowledge API, Annual Report Linker.
* **Extraction Engine**: Firecrawl Deep Content Extractor.

### Provider Independence Principle
Search providers **discover** information; the underlying publishing source determines **authority**. Multiple search engines returning the same article (e.g., Tavily $\rightarrow$ Reuters, Serper $\rightarrow$ Reuters) represent **one underlying source (Reuters)**, not independent confirmations.

---

## 6. Source Authority Hierarchy

| Tier | Category | Authoritative Sources | Authority Score |
| :---: | :--- | :--- | :---: |
| **Tier 1** | **Government & Statutory Filings** | IRDAI, SEC/EDGAR, NAIC, FCA, Official Annual Reports, Audited Disclosures, Investor Presentations | **0.95 – 1.00** |
| **Tier 2** | **Stock Exchanges & Rating Agencies** | NSE, BSE, NYSE, LSE, CRISIL, ICRA, CARE, AM Best, Moody's, S&P Global, Fitch, Screener, Moneycontrol | **0.80 – 0.90** |
| **Tier 3** | **Major Financial & Business Press** | Bloomberg, Reuters, Financial Times, Wall Street Journal, Economic Times, Livemint, Business Standard, Insurance Journal | **0.65 – 0.80** |
| **Tier 4** | **General Web & Industry Portals** | General news outlets, industry research portals, trade websites | **0.40 – 0.60** |
| **Tier 5** | **Discovery & Low-Authority Sites** | Blogs, forums, Medium, Reddit, Quora, unverified aggregators | **0.35** |

Lower-tier sources have their authority downgraded when stronger Tier 1–3 evidence exists.

---

## 7. Parameter-Specific Source Priority

Source weighting adapts dynamically based on the parameter:
* **Financial Strength**: Regulatory filings > Audited Annual Reports > Rating Agencies > Financial Databases > Major Financial Press.
* **Business Growth**: Annual Reports > Quarterly Investor Presentations > Financial Results > Business Press.
* **Market Position**: Regulatory Market Share Reports > Annual Disclosures > Industry Research > Major Business News.
* **Insurance Performance**: IRDAI / Statutory Disclosures > Audited Disclosures > Rating Agencies > Industry Press.
* **Technology Activity**: Official Corporate Disclosures > Technology Press > Case Studies > Industry Portals.
* **Strategic Activity / M&A**: Stock Exchange Filings > Regulatory Announcements > Corporate Disclosures > Reuters / Bloomberg.

---

## 8. Duplicate Handling Rules

### Rule 8.1: Fact / Value Deduplication
When two or more sources report the identical factual value (e.g., *Reuters: Solvency Ratio 220%* and *Annual Report: Solvency Ratio 220%*):
* The factual statement is displayed **only once**: `Solvency Ratio: 220%`
* Both supporting sources are retained as citations: `[Official Annual Report] [Reuters]`

### Rule 8.2: Duplicate URL Normalization
URLs are normalized before comparison by:
1. Stripping tracking parameters (`utm_*`, `gclid`, `fbclid`, `ref`, `session_id`, `source`).
2. Removing URL fragments/anchors (`#...`).
3. Standardizing protocols and lowercasing domain names (stripping `www.`).
4. Stripping trailing slashes.

### Rule 8.3: Content Similarity & Syndication Detection
Syndicated news articles and republished press releases across different URLs are detected through title and content similarity and consolidated, preventing artificial inflation of confirmation counts.

---

## 9. Conflict Resolution Hierarchy (Zero Value Averaging)

When two trustworthy sources report conflicting data for the **same period**:
1. **Never Average**: Mathematical averaging creates fabricated, non-existent data points and is strictly prohibited.
2. **Authority Hierarchy**:
   1. Current statutory / regulatory filing (Tier 1)
   2. Audited annual report (Tier 1)
   3. Official company investor disclosure (Tier 1)
   4. Stock exchange disclosure (Tier 2)
   5. Recognized financial database / rating agency (Tier 2)
   6. Bloomberg / Reuters / FT (Tier 3)
   7. Established industry publication (Tier 3)
   8. General web source (Tier 4)
3. **Temporal Awareness**: Values from different fiscal years (e.g., `FY2024 Revenue: $9B` vs. `FY2025 Revenue: $10B`) are indexed as time-series metrics and **never treated as conflicts**.
4. **Unit & Currency Awareness**: Values are reconciled against currency (USD vs. INR), unit (Million vs. Billion vs. Crore), and metric definition (GAAP vs. Adjusted).
5. **Transparency Discrepancy Note**: If two Tier 1 or Tier 2 sources report differing numbers for the same period, both are retained, the higher authority/more recent is prioritized, and an explicit discrepancy notice is generated with both citations:
   > *"⚠️ Discrepancy Note: Q3 Operating Profit is reported as \$500M (SEC 10-Q) vs. \$620M (Adjusted EBITDA, Investor Presentation)."*

---

## 10. Citation & Output Quality Standards

### Rule 10.1: Citation Limits
* **Per Parameter**: 3 to 5 strongest, most authoritative sources displayed.
* **Per Individual Fact**: 2 to 4 high-quality supporting citations displayed beside the fact.

### Rule 10.2: Missing Data Protocol
If reliable evidence is absent for a parameter, the system must output:
> *"Insufficient reliable evidence was found for this parameter."*
Generic placeholder filler (e.g., *"Verified empirical disclosures recorded..."*) is prohibited.

### Rule 10.3: No-Hallucination Mandate
The LLM serves as an **evidence interpreter and summarizer**, not an evidence creator. All financial figures, dates, ratios, customer counts, and URLs must originate strictly from harvested evidence.

---

## 11. Final Output Contract

```json
{
  "parameter": "Business Growth",
  "summary": "Evidence-backed parameter summary detailing YoY expansion and metrics.",
  "key_facts": [
    {
      "fact": "Gross Written Premium expanded by 14.8% YoY to INR 28,450 Crore in FY2025.",
      "sources": [
        {
          "name": "Official Annual Report FY25",
          "url": "https://www.sbilife.co.in/annual-report-fy25",
          "evidence": "GWP stood at INR 28,450 Crore reflecting 14.8% YoY growth."
        },
        {
          "name": "Reuters",
          "url": "https://www.reuters.com/business/sbi-life-fy25-growth",
          "evidence": "SBI Life reports 14.8% rise in gross premium."
        }
      ]
    }
  ],
  "sources": [
    {
      "name": "Official Annual Report FY25",
      "url": "https://www.sbilife.co.in/annual-report-fy25",
      "evidence": "GWP stood at INR 28,450 Crore reflecting 14.8% YoY growth."
    }
  ],
  "conflicts": [],
  "confidence": "High",
  "score": 88
}
```

---

## 12. The 20 Golden Rules

1. **RULE 1**: Never invent data.
2. **RULE 2**: Never invent citations.
3. **RULE 3**: Never mix prospects.
4. **RULE 4**: Never mix unrelated parameters.
5. **RULE 5**: Same value $\rightarrow$ display once.
6. **RULE 6**: Same value + multiple trustworthy sources $\rightarrow$ display value once + retain multiple citations.
7. **RULE 7**: Same URL from multiple search providers $\rightarrow$ count as one underlying source.
8. **RULE 8**: Different trustworthy sources with conflicting values $\rightarrow$ do not arbitrarily discard evidence.
9. **RULE 9**: Resolve conflicts using authority + recency + reporting period + relevance + direct evidence (no averaging).
10. **RULE 10**: Different reporting periods are not automatically conflicts.
11. **RULE 11**: Prefer primary/official sources for factual verification.
12. **RULE 12**: Search providers discover sources; they do not determine truth.
13. **RULE 13**: Firecrawl extracts content; it does not establish source authority.
14. **RULE 14**: LLM interprets evidence; it does not invent evidence.
15. **RULE 15**: If evidence is insufficient, explicitly say so.
16. **RULE 16**: Every important factual claim should be traceable to evidence.
17. **RULE 17**: Optimize for evidence quality, not number of search results.
18. **RULE 18**: Do not count duplicate syndicated articles as independent confirmations.
19. **RULE 19**: Do not let a single provider failure invalidate the entire analysis.
20. **RULE 20**: Do not change the existing architecture to implement these rules.

---

## 13. Acceptance Test Scenarios

* **Test A — Prospect Scope**: Supported prospect accepted; unsupported prospect rejected.
* **Test B — Exact Prospect Identity**: HDFC Life research strictly excludes ICICI Prudential evidence.
* **Test C — Duplicate Value**: Revenue = \$10B from 2 sources displayed once with 2 citations.
* **Test D — Duplicate URL**: Tavily & Serper returning same URL treated as 1 source.
* **Test E — Conflicting Trustworthy Sources**: Reuters vs Bloomberg discrepancy detected, preferred source selected, both citations available.
* **Test F — Different Reporting Periods**: FY2024 vs FY2025 treated as distinct metrics without conflict.
* **Test G — Official Source vs Low-Authority Source**: Tier 1 official source ranked higher than Tier 5 blog.
* **Test H — Missing Evidence**: Returns "Insufficient reliable evidence" without generic filler.
* **Test I — Multiple Citations**: Fact supported by Annual Report & Reuters displays both citations.
* **Test J — Prospect Contamination**: Sequential execution of HDFC Life and ICICI Lombard ensures zero cross-prospect evidence leakage.
