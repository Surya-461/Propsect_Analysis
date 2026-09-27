# Prospect AI: Executive Presentation Guide
## Rules, Constraints & Output Governance Framework

**Presentation Target:** Executive Leadership, Underwriting Committees, Product & Engineering Stakeholders  
**Classification:** Enterprise Operational & Governance Standard  
**Platform:** Prospect AI Underwriting Intelligence Platform  

---

# Executive Summary

The **Prospect AI Output Governance Framework** enforces deterministic, evidence-grounded rules over public data aggregation, LLM synthesis, and report presentation. 

### Core Presentation Thesis
> **"Accuracy and traceability always take precedence over simply producing a populated response. The system never invents numbers, never averages conflicting facts, never mixes competitor data, and treats every factual assertion as an auditable claim."**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           THE GOVERNANCE PIPELINE                           │
│                                                                             │
│  User Request ──► [ Bounded Scope Gate ] ──► [ Multi-Source Discovery ]     │
│  (SBI Life)       • 250-300 Catalog          • Tavily / Serper / RSS        │
│                   • Canonical Entity         • URL Normalization            │
│                                                                             │
│  [ Output Presentation ] ◄── [ LLM Interpreter ] ◄── [ Evidence Governance ]│
│  • Deduplicated Facts        • Gemini / Ollama       • 5-Tier Authority     │
│  • Multi-Citations           • Strict Grounding      • Zero-Averaging       │
│  • Discrepancy Alerts        • No Hallucination      • Period Awareness     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Slide 1: The 20 Golden Rules of Prospect Intelligence

When presenting the platform's reliability guarantees, highlight these **20 Immutable Golden Rules**:

| # | Rule Name | Operational Rule |
| :---: | :--- | :--- |
| **1** | **No Inventions** | Never invent financial figures, metrics, dates, or acquisitions. |
| **2** | **No Fake Citations** | Never generate or synthesize unverified URLs or source titles. |
| **3** | **Prospect Isolation** | Never mix evidence between different companies (e.g., HDFC vs. SBI Life). |
| **4** | **Parameter Isolation** | Never mix unrelated parameters (e.g., Financial Strength vs. Tech). |
| **5** | **Single Fact Display** | If multiple sources report the same value, display the value **only once**. |
| **6** | **Multi-Citation Retention** | Display the deduplicated fact once, but attach **2–4 supporting citations**. |
| **7** | **URL Normalization** | The same URL from Tavily, Serper, and RSS counts as **one underlying source**. |
| **8** | **Conflict Preservation** | When trustworthy sources disagree, retain both in evidence (never drop silently). |
| **9** | **Zero Averaging** | Resolve conflicts by authority and recency; **never calculate an average**. |
| **10** | **Period Awareness** | Different fiscal periods (FY24 vs. FY25) are **time series, not conflicts**. |
| **11** | **Primary Source Priority** | Prefer statutory filings and audited annual reports over news aggregators. |
| **12** | **Provider Role Clarity** | Search engines discover information; the publisher determines authority. |
| **13** | **Firecrawl Role Clarity** | Firecrawl is a content extraction tool, not an independent authority. |
| **14** | **LLM Role Clarity** | The LLM interprets and explains evidence; the research engine supplies evidence. |
| **15** | **Uncertainty Transparency** | If evidence is absent, output *"Insufficient reliable evidence was found."* |
| **16** | **Traceability Mandate** | Every important factual assertion must be directly traceable to a source. |
| **17** | **Quality over Quantity** | Optimize for high-authority disclosures rather than high search count. |
| **18** | **Syndication Detection** | Republished press release clones are not counted as independent confirmations. |
| **19** | **Provider Resilience** | A timeout in one provider (e.g., Firecrawl) must not fail the overall analysis. |
| **20** | **Architecture Stability** | Implement all governance rules on top of the established architecture. |

---

# Slide 2: Input Scope Constraint & Entity Resolution

### The Problem
Traditional AI assistants allow users to query arbitrary string prompts, leading to crawling junk websites, hallucinations, and non-corporate entities.

### The Solution: Bounded 250–300 Carrier Directory
1. **Authoritative Universe**: Research is restricted to a curated directory of **250+ verified insurers** (`insurance_prospects_250.json`).
2. **Canonical Matching**: Multi-variant entity resolution (e.g., `"SBI Life"` $\rightarrow$ `"SBI Life Insurance Company Limited"`, `"LIC"` $\rightarrow$ `"Life Insurance Corporation of India"`).
3. **Ambiguity Disambiguation**: Queries matching multiple entities (e.g., `"SBI"`) trigger interactive selection cards.
4. **Deterministic Rejection**: Unsupported entities receive a clear, defensive response:
   > *"This prospect is not currently supported. Please select a company from the supported prospect list."*

---

# Slide 3: 5-Tier Source Authority Hierarchy

Not all web pages are equal. Sources are automatically classified into 5 distinct authority tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: Statutory & Regulators (Weight: 0.95 - 1.00)                   │
│ IRDAI, SEC EDGAR, NAIC, Audited Annual Reports, Investor Presentations │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: Stock Exchanges & Rating Agencies (Weight: 0.80 - 0.90)        │
│ NSE, BSE, CRISIL, ICRA, CARE, AM Best, Moody's, Screener, Moneycontrol │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: Established Financial Press (Weight: 0.65 - 0.80)              │
│ Bloomberg, Reuters, Financial Times, WSJ, Economic Times, Livemint     │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 4: General Web & Industry Portals (Weight: 0.40 - 0.60)           │
│ General news sites, regional publications, industry portals           │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 5: Low-Authority Discovery Sources (Weight: 0.35)                 │
│ Blogs (Medium, Substack), forums (Reddit, Quora), content aggregators  │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Presentation Talking Point:
> **"Lower-tier sources are never automatically believed over Tier 1 statutory disclosures. When official filings exist, lower-tier web noise is downgraded automatically."**

---

# Slide 4: Parameter-Specific Source Priority

Authority weighting adjusts dynamically depending on the specific underwriting dimension:

| Parameter | Preferred Authoritative Sources |
| :--- | :--- |
| **Financial Strength** | Regulatory filings, Audited Annual Reports, CRISIL/ICRA Ratings, Balance Sheets |
| **Insurance Performance** | IRDAI Disclosures, Combined Ratio Disclosures, Actuarial Reports |
| **Business Growth** | Investor Presentations, Financial Results, GWP Growth Disclosures |
| **Market Position** | Statutory Market Share Tables, Industry Peer Rankings |
| **Operational Scale** | Corporate Filings, Distribution Network & Branch Disclosures |
| **Technology Activity** | Official Corporate Tech Announcements, Press Releases, Core Modernization Reports |
| **Strategic Activity** | Stock Exchange Disclosures, Regulatory Approval Announcements, M&A Filings |

---

# Slide 5: Fact Deduplication & Multi-Citation Behavior

### The Challenge
When multiple independent sources report the same key metric (e.g., Solvency Ratio = 220%), naive AI systems repeat the bullet points multiple times or only attribute one random source.

### The Governance Standard (Rules 5 & 6)
* **Single Statement**: The factual value is displayed **exactly once**.
* **Multiple Clickable Citations**: 2 to 4 high-quality supporting citations are attached to that single fact.

```
┌────────────────────────────────────────────────────────────────────────┐
│ BEFORE (Naive Pipeline):                                              │
│ • Solvency ratio was reported as 220% [Reuters]                       │
│ • Solvency ratio was 220% [Annual Report]                             │
│ • Solvency ratio reached 220% [IRDAI Filing]                          │
├────────────────────────────────────────────────────────────────────────┤
│ AFTER (Prospect AI Governance):                                       │
│ • Solvency ratio stood at 220% as of March 2025.                      │
│   [Official Annual Report FY25] [IRDAI Statutory Filing] [Reuters]     │
└────────────────────────────────────────────────────────────────────────┘
```

---

# Slide 6: Conflict Resolution & Zero Averaging

### Rule 1: Zero Averaging
> **If Reuters reports Revenue at $10.0B and Bloomberg reports $9.8B, calculating $9.9B is forbidden. $9.9B is a hallucinated number that neither organization published.**

### Rule 2: Temporal & Unit Disambiguation
* **Different Periods $\neq$ Conflict**: `FY2024: INR 16,000 Cr` and `FY2025: INR 18,500 Cr` are recognized as historical time series.
* **Currencies & Units**: Reconciled across INR/USD and Million/Billion/Crore.

### Rule 3: Transparent Discrepancy Reporting
When two Tier 1/2/3 sources report differing values for the same fiscal period:
1. Both evidence records are retained.
2. The higher-tier / latest source is prioritized.
3. An explicit **Discrepancy Notice** is generated:

```
⚠️ Discrepancy Notice:
Conflicting authoritative information was found for Revenue (FY2025):
USD 10.00 Billion (Reuters) vs. USD 9.80 Billion (Bloomberg).
The official filing reporting USD 10.00 Billion has been prioritized.
```

---

# Slide 7: Missing Data & Anti-Contamination Guardrails

### 1. Missing Data Handling (Rule 15)
If public disclosures do not contain reliable data for a parameter, the system explicitly states:
> **"Insufficient reliable evidence was found for this parameter."**
The system **never** outputs generic filler phrases such as *"Verified empirical disclosures recorded."*

### 2. Prospect Anti-Contamination (Rule 3)
* Every harvested item is tagged with its canonical prospect ID.
* Competitor filtering prevents rival entities from contaminating analysis (e.g., an ICICI Prudential news story is never displayed under HDFC Life).

### 3. LLM vs. Research Engine Separation
* **Research Engine (Deterministic)**: Discovers, normalizes URLs, extracts text, calculates authority scores, deduplicates values, and reconciles conflicts.
* **LLM Engine (Synthesis)**: Explains, summarizes, and synthesizes natural language strictly from curated evidence.

---

# Slide 8: Verification & Acceptance Test Suite

The entire governance architecture is backed by an automated 10-scenario acceptance test suite (`test_output_governance.py`):

```
┌────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE TEST MATRIX                                                 │
│                                                                        │
│  [Test A] Prospect Scope ──────────► Supported accepted / Unknown rejected │
│  [Test B] Exact Identity ──────────► HDFC Life excludes ICICI Pru data │
│  [Test C] Duplicate Value ─────────► Same fact displayed once with 2 srcs │
│  [Test D] Duplicate URL ───────────► Multi-engine URLs merged into 1  │
│  [Test E] Conflicting Sources ─────► Discrepancy alert + zero averaging│
│  [Test F] Different Periods ───────► FY24 vs FY25 treated as time series│
│  [Test G] Authority Ranking ───────► Tier 1 Regulator > Tier 5 Blog   │
│  [Test H] Missing Evidence ────────► Standardized Insufficient notice  │
│  [Test I] Multi-Citation ──────────► 1 Fact with [Annual Report][Reuters]│
│  [Test J] Contamination Gate ──────► HDFC -> ICICI zero bleed         │
│                                                                        │
│  RESULT: 79 / 79 Test Cases Passed (100% Green)                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

# Slide 9: Executive Presentation Q&A Talking Points

### Q: "How do we guarantee the LLM does not hallucinate revenue or solvency numbers?"
> **Answer:** "The LLM never performs web searches on its own. All evidence is first harvested, parsed, deduplicated, and ranked by our deterministic research pipeline. The LLM only receives verified extracted facts and is strictly instructed to synthesize only provided disclosures."

### Q: "What happens if a news blog contradicts an official IRDAI / SEC filing?"
> **Answer:** "Our 5-Tier Authority Ranker assigns Tier 1 (1.00 weight) to statutory filings and Tier 5 (0.35 weight) to blogs. The official filing automatically overrides the blog without manual intervention."

### Q: "Why don't we average conflicting figures to find a middle ground?"
> **Answer:** "In institutional underwriting, averaging conflicting data creates an invented figure that has zero statutory standing. We report the authoritative number, preserve the competing source, and transparently display a discrepancy notice."

### Q: "How does the system handle multi-search provider redundancy (Tavily + Serper)?"
> **Answer:** "We normalize URLs by stripping tracking parameters, session IDs, and fragments. If Tavily and Serper return the same Reuters article, the system counts it as one underlying source, preserving true independent confirmation."

---

# Presentation Deck Summary Cheat Sheet

| Core Pillar | Specification Rule | Implementation |
| :--- | :--- | :--- |
| **Catalog Scope** | 250–300 Verified Insurers | `ProspectValidationGateway` |
| **Source Authority** | 5-Tier Weighted Taxonomy | `authority_ranker.py` |
| **Duplicate Values** | Value Displayed Once + Multi-Citations | `output_governor.py` |
| **Duplicate URLs** | Normalized Domain Consolidation | `normalizer.py` |
| **Conflicts** | Zero Averaging + Discrepancy Alerts | `conflict_resolver.py` |
| **Temporal Dates** | FY24 vs FY25 Time Series | Period Regex & Currency Matcher |
| **Missing Data** | "Insufficient reliable evidence" Notice | `summarizer.py` & Guardrails |
| **Verification** | 10 Automated Acceptance Tests (A to J) | `test_output_governance.py` (79/79 Passed) |
