# Prospect Intelligence Platform: Constraints, Rules & Output Governance Specification

**Document Version:** 1.0  
**Classification:** Technical & Operational Specification  
**Scope:** Input Validation, Multi-Source Aggregation, Data Conflict Resolution, Deduplication, Citation Attribution, and Output Synthesis Governance.

---

## 1. Executive Summary & Purpose

This specification defines the authoritative set of **business constraints**, **data governance rules**, and **algorithmic resolution strategies** enforced by the **Prospect Intelligence Platform** during the ingestion, synthesis, and presentation of prospect analysis reports.

These rules ensure that every generated output is **empirically grounded**, **deterministic**, **defensible under underwriting standards**, and free from hallucinated or ungrounded claims.

---

## 2. Input Validation & Prospect Scope Constraints

```
┌───────────────────────────────────────────────────────────────────────┐
│                       INPUT VALIDATION GATEWAY                        │
│                                                                       │
│  User Input  ──► [ Sanity Checks ] ──► [ 250 Prospect Catalog ]       │
│  (Company)        • 2 - 250 chars       • Exact ID Match              │
│                   • Non-empty           • Alias / Legal Name Match    │
│                   • Insurance Domain    • Fuzzy Normalization         │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
   [ Valid Prospect ]                             [ Ambiguous / Invalid ]
   • Proceed to Research Pipeline                  • Multiple: Disambiguation Card
   • Isolated Context Session                      • Unknown: Rejection + Suggestions
```

### Constraint 2.1: Bounded 250 Insurance Prospect Directory
* **Rule:** System analysis is strictly bounded to an authoritative catalog of **250 verified insurance carriers and financial institutions** (`insurance_prospects_250.json`).
* **Rationale:** Eliminates entity hallucination, prevents crawling arbitrary or non-corporate web pages, and ensures only legitimate insurance market prospects with verifiable statutory filings are processed.

### Constraint 2.2: Input Text Sanity Checks
* **Minimum Length:** Input must contain at least **2 characters**.
* **Maximum Length:** Input cannot exceed **250 characters**.
* **Domain Standard:** Validated under the `Insurance` underwriting domain schema.

### Constraint 2.3: Deterministic Entity Resolution & Disambiguation
* **Direct Match:** Exact match against primary name or canonical ticker/ID (e.g., `HDFC_ERGO` $\rightarrow$ "HDFC ERGO General Insurance Company").
* **Alias Matching:** Multi-variant resolution (e.g., `"SBI Life"` $\rightarrow$ `"SBI Life Insurance Company Limited"`).
* **Ambiguous Resolution:** When a query matches multiple valid entities (e.g., `"SBI"` could mean *SBI Life Insurance* or *SBI General Insurance*), the system suspends analysis and emits a structured **Disambiguation Choice Card** with selectable options.
* **Unrecognized Entities:** Inputs outside the directory receive a clear validation notice accompanied by suggested supported carriers (e.g., *"SBI Life Insurance"*, *"Allianz"*, *"AXA"*, *"ICICI Lombard"*).

---

## 3. Multi-Source Hierarchy & Authority Weighting

When harvesting public data (statutory filings, corporate portals, news feeds, financial databases, regulatory registries), sources are assigned an **Authority Tier**:

| Tier | Category | Sources / Registries | Authority Weight ($w_{\text{source}}$) |
| :---: | :--- | :--- | :---: |
| **Tier 1** | **Statutory & Legal Registries** | SEC EDGAR, IRDAI, UK Companies House, State Insurance Depts, Audited 10-K/Annual Disclosures | **0.95 – 1.00** |
| **Tier 2** | **1st-Party Corporate Disclosures** | Official Corporate Investor Relations, Official Press Releases, Corporate Governance Disclosures | **0.80 – 0.90** |
| **Tier 3** | **Reputable Financial & News Media** | Bloomberg, Reuters, Wall Street Journal, Financial Times, Associated Press | **0.65 – 0.80** |
| **Tier 4** | **Public Aggregators & Signals** | Wikipedia, LinkedIn, Glassdoor, Industry Blogs, General Web Search | **0.40 – 0.60** |

---

## 4. Data Conflict Resolution Rules

Data conflicts frequently arise when aggregating data across heterogeneous public channels. The system executes the following deterministic conflict resolution policies:

### Rule 4.1: Source Authority Hierarchy Precedence
* **Rule:** If a higher-tier source contradicts a lower-tier source on the same metric for the same reporting period, **the higher-tier source takes automatic precedence**.
* **Example:** If an SEC 10-K filing reports total headcount at **4,200** and Wikipedia reports **3,500**, the SEC filing (Tier 1) overrides Wikipedia (Tier 4).

### Rule 4.2: Temporal Alignment & Reporting Period Matching
* **Rule:** Data points belonging to different fiscal periods or effective dates are **never treated as conflicting values**.
* **Action:** Values are indexed by their respective fiscal periods (e.g., `FY2023 Revenue: INR 168,731M` and `FY2024 Run-Rate: INR 205,000M`). Both remain valid as time-series metrics rather than overwriting each other.

### Rule 4.3: Contradiction Between Equally Trustworthy Sources (Tier 1 vs. Tier 1)
* **Rule:** When two equally trustworthy sources (such as *Bloomberg vs. Reuters*, or *SEC Filing vs. Official Corporate Press Release*) report contradictory data for the same period:
  1. **No Arbitrary Discarding:** The automated pipeline **never silently drops or randomly selects** one value over the other.
  2. **No Averaging:** The system **never calculates a mathematical average** of conflicting numbers (which creates an ungrounded, non-existent data point).
  3. **Dual Attribution / Side-by-Side Reporting:** The output presents both values with their respective source citations and dates.
  4. **Transparency Notice:** A structured discrepancy note is generated:
     > *"⚠️ Discrepancy Note: Q3 Operating Profit is reported as \$500M (GAAP, SEC 10-Q) vs. \$620M (Adjusted EBITDA, IR Press Release)."*

### Rule 4.4: Semantic & Accounting Standard Disambiguation
* **Rule:** Before flagging a numerical variance as a factual conflict, the system evaluates definition schemas:
  * **GAAP vs. Non-GAAP / IFRS** (Operating Income vs. Adjusted EBITDA).
  * **FTE vs. Total Headcount** (Full-Time Equivalents vs. inclusive contractor staff).
  * **Gross vs. Net Premium** (GWP vs. NWP).
* Metrics matching distinct definitions are mapped to distinct sub-attributes.

### Rule 4.5: Triangulation & Consensus Majority Voting
* **Rule:** If three or more independent sources on the same tier report on a non-statutory parameter and an outlier occurs, the system accepts the majority consensus (e.g., 3 out of 4 sources agree on an acquisition date) and suppresses the isolated outlier.

---

## 5. Data Deduplication & Identical Value Rules

### Rule 5.1: Fact Deduplication
* **Rule:** When two or more sources provide the **exact same data point** (e.g., *"Solvency Ratio: 2.15x"*), the data value itself is **deduplicated and displayed only once** in the output report.
* **Benefit:** Prevents redundant repetition in the UI, keeping executive summaries concise and readable.

### Rule 5.2: Confidence Corroboration Boost
* **Rule:** When independent sources corroborate the same fact, the system calculates a **corroboration boost** on the confidence score:
  $$\text{Confidence} = \min(1.0, S_{\text{base}} + 0.15 \times (N - 1))$$
  *(where $N$ is the number of agreeing independent sources).*

---

## 6. Source Attribution & Citation Display Strategies

When outputting verified facts, citation links are presented according to the following standard strategies:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      CITATION STRATEGY TAXONOMY                        │
├────────────────────────────────┬───────────────────────────────────────┤
│ Strategy                       │ Behavioral Logic                      │
├────────────────────────────────┼───────────────────────────────────────┤
│ 1. Multi-Source Corroboration  │ Displays citations for all agreeing   │
│    (Standard Default)          │ sources (e.g. [SEC 10-K, IR Portal])  │
├────────────────────────────────┼───────────────────────────────────────┤
│ 2. Highest-Authority Selection │ When single link required: Selects    │
│    (Tier 1 Priority)           │ the highest trust tier registry       │
├────────────────────────────────┼───────────────────────────────────────┤
│ 3. Recency / Freshness Rule    │ Among equal tiers: Selects the most   │
│    (Latest Timestamp)          │ recently published/crawled citation   │
├────────────────────────────────┼───────────────────────────────────────┤
│ 4. Grounded Snippet Evidence   │ Links citation to verbatim verified   │
│    (Deep Verification)         │ text excerpt from the public source   │
└────────────────────────────────┴───────────────────────────────────────┘
```

* **Standard Output Format:** Every key fact item links to its verified URL and displays a grounded text snippet:
  > • **Gross Written Premium:** INR 168,731.4M in FY2023  
  >   *Source:* `[IRDAI Statutory Disclosures]` *(Evidence: "Gross direct premium income reached INR 168,731.4 million in FY2023...")*

---

## 7. Output Structure & Parameter Governance Constraints

### Constraint 7.1: The 8 Standard Underwriting Parameters
Every comprehensive prospect analysis must analyze and structure findings across the 8 core parameters:

1. **Company Scale:** Core business lines, incorporation history, enterprise scale, geographic presence.
2. **Business Growth:** Revenue trajectories, GWP growth rates, AUM progression, CAGR.
3. **Market Position:** Market share percentages, industry ranking, peer competitive positioning.
4. **Financial Strength:** Solvency ratios, balance sheet reserves, credit ratings (e.g., ICRA, CRISIL, AM Best).
5. **Insurance Performance:** Combined ratios, loss ratios, claims settlement ratios, underwriting profitability.
6. **Operational Scale:** Employee headcount, branch networks, agency distribution, policyholder base.
7. **Technology Activity:** Core system modernization, AI underwriting integration, digital claims, cloud deployments.
8. **Regulatory & Compliance Disclosures:** Regulatory standing, IRDAI/SEC statutory disclosures, audit observations.

### Constraint 7.2: Text Length & Quality Guardrails
* **Executive Summary:** Synthesized within **4 to 8 high-density sentences** (maximum 1,400 characters).
* **Key Facts per Parameter:** Maximum **8 bullet points** containing high-signal empirical facts.
* **Noise Suppression:** Zero raw table dumps, stripped HTML tags, normalized currency notations (`INR` / `USD`), and elimination of navigation fragments (e.g., *"Click here"*, *"Form A-1"*, *"Select Year"*).

---

## 8. User Authentication & OAuth 2.0 Security Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                      OAUTH 2.0 & JWT AUTH PIPELINE                     │
│                                                                        │
│  [ React Frontend ] ──► Google One Tap / Sign-In Popup                 │
│         │                │ (ID Token / Access Token)                   │
│         ▼                ▼                                             │
│  POST /auth/google ──► [ Backend Auth Service ]                        │
│                          │ • Verify via Google OAuth2 tokeninfo API   │
│                          │ • Upsert User Record in PostgreSQL          │
│                          │ • Issue Signed JWT Bearer Token             │
│                          ▼                                             │
│  Protected Endpoints ──► [ User-Isolated Multi-Tenant Database ]       │
│  (/analyze, /chat)        • analyses WHERE user_id = current_user.id   │
└────────────────────────────────────────────────────────────────────────┘
```

### Rule 8.1: Google OAuth 2.0 Token Verification
* **Endpoint:** `POST /api/auth/google`
* **Mechanism:** The backend receives the Google ID Token or Access Token from the client and verifies its authenticity server-side using Google's authoritative endpoint:
  ```text
  https://oauth2.googleapis.com/tokeninfo?id_token=<CREDENTIAL>
  ```
* **Payload Verification:** Validates signature, audience (`aud`), expiration (`exp`), and extracts verified user identity (`email`, `name`, `picture`, `sub`).

### Rule 8.2: JWT Session Token Issuance & Route Protection
* **Token Standard:** Issues signed **JWT Bearer Tokens** (HMAC-SHA256) containing `sub` (User ID), `email`, and expiration timestamp.
* **Route Protection:** All analysis and chat endpoints (`/api/analyze`, `/api/chat`, `/api/analyses`, `/api/prospects/resolve`) require the `Authorization: Bearer <token>` header, enforced via FastAPI dependency injection (`get_current_user`).

### Rule 8.3: Tenant & User History Isolation
* **Data Privacy Constraint:** Analysis reports, prospect switching history, and chat logs are strictly partitioned per authenticated user.
* **SQL Query Enforcement:** All queries filter strictly by `WHERE user_id = current_user.id`. Users cannot view, modify, or delete other users' intelligence reports.

---

## 9. Dynamic External API Ingestion Pipeline (Serper, Tavily, Firecrawl)

```
┌────────────────────────────────────────────────────────────────────────┐
│                 DYNAMIC MULTI-SOURCE INGESTION ENGINE                  │
│                                                                        │
│  Analysis Request ──► [ Parameterized Query Generator ]                │
│                            │                                           │
│       ┌────────────────────┼────────────────────┐                      │
│       ▼                    ▼                    ▼                      │
│  [ Serper.dev API ]  [ Tavily Search ]  [ Firecrawl Crawler ]          │
│  • Google Search     • Deep Fact Search • Web Content Extractor        │
│  • Organic Results   • Knowledge Base   • Markdown Parsing             │
│       │                    │                    │                      │
│       └────────────────────┬────────────────────┘                      │
│                            ▼                                           │
│             [ Evidence Normalization Engine ]                          │
│             • Extract Title, Snippet, URL, Date, Domain                │
│             • Assign Source Authority Tier (1 to 4)                    │
│             • Deduplicate & Feed to Conflict Resolver                  │
└────────────────────────────────────────────────────────────────────────┘
```

### Rule 9.1: Serper.dev Google Search API Integration
* **API Role:** Primary web discovery engine for live statutory disclosures, press releases, rating reports, and business developments.
* **Implementation:**
  * Endpoint: `https://google.serper.dev/search`
  * Headers: `X-API-KEY: <SERPER_API_KEY>`, `Content-Type: application/json`
  * Country / Language Targeting: `gl: "in"` (or target jurisdiction), `hl: "en"`
* **Targeted Query Generation:** The query generator formats parameter-specific search strings for each of the 8 underwriting dimensions:
  * *Scale:* `"{prospect_name} annual report GWP revenue total income"`
  * *Financial Strength:* `"{prospect_name} solvency ratio ICRA CRISIL rating balance sheet"`
  * *Insurance Performance:* `"{prospect_name} combined ratio loss ratio claims settlement IRDAI"`
  * *Tech & Ops:* `"{prospect_name} digital transformation AI underwriting core systems"`

### Rule 9.2: Collector Resilience & Failover Cascade
* **Cascade Chain:** If primary Serper search experiences rate limits or network timeout, the engine fails over to **Tavily Search API** $\rightarrow$ **Firecrawl Crawler** $\rightarrow$ **Static Curated Statutory Filings**.
* **Evidence Normalization:** Raw JSON responses are parsed and converted into uniform `Evidence` schema objects:
  ```python
  Evidence(
      parameter="Financial Strength",
      title="HDFC ERGO Solvency Ratio and Capital Adequacy Disclosures",
      content="The insurer maintained a solvency ratio of 1.68x against regulatory minimum...",
      source_url="https://www.hdfcergo.com/financial-disclosures",
      source_name="hdfcergo.com",
      source_tier=1,
      timestamp=datetime.now()
  )
  ```

---

## 10. Prompt Engineering Architecture & AI Output Synthesis

The platform employs a two-tier prompt engineering architecture (System Prompt + Parameterized Extraction Prompts) powering **Google Gemini 2.5 / Flash** and **Ollama** models:

### Rule 10.1: Master System Prompt (Operational Persona & Boundaries)
The system prompt establishes the behavioral identity, domain expertise, and zero-hallucination mandate:

```text
You are an INSURANCE INTELLIGENCE ANALYST & UNDERWRITING SPECIALIST with expertise in:
- Enterprise risk assessment and underwriting standards
- Financial analysis and corporate structure evaluation
- Industry benchmarking and market positioning

CRITICAL OPERATIONAL RULES:
1. GROUND ALL STATEMENTS in provided data (public sources, reports, evidence).
2. CITE every fact with source URL and publication date.
3. NEVER invent or hallucinate data, metrics, or financial figures.
4. USE PRECISE LANGUAGE - distinguish between "confirmed facts" and "signals".
5. DISCLOSE DATA GAPS - clearly state what information is unavailable.
6. MAINTAIN PROFESSIONAL TONE suitable for underwriting committees.
7. PRIORITIZE ACCURACY over completeness - incomplete data is better than false data.
```

### Rule 10.2: Structured Parameter Extraction Prompt Template
For each of the 8 parameters, raw normalized evidence is injected into a strict JSON-enforced synthesis template:

```text
TARGET COMPANY: {company_name}
ANALYSIS PARAMETER: {parameter}
COLLECTION TIMESTAMP: {timestamp}

PROVIDED DATA SOURCES:
{source_evidence_items}

TASK: Provide structured analysis grounded strictly in the provided sources.

REQUIRED OUTPUT FORMAT (Valid JSON):
{
    "summary": "2-4 sentence executive synthesis grounded in provided data only",
    "confidence_level": "High/Medium/Low based on data quality and completeness",
    "key_facts": [
        "Empirical Fact 1 (Source: Name | URL)",
        "Empirical Fact 2 (Source: Name | URL)"
    ],
    "sources": [
        {"name": "Source Name", "url": "https://...", "evidence": "Direct excerpt"}
    ],
    "data_gaps": ["Optional missing information notes"]
}
```

### Rule 10.3: Anti-Hallucination & Anti-Leakage Post-Processing Guardrails
* **Fact Noise Filter:** Snippets containing pure table dumps, navigation artifacts (*"Form A-1"*, *"Select Year"*), or OCR distortions are stripped before LLM ingestion.
* **Sentence & Length Clamping:** Post-processors enforce a hard maximum of **8 high-density sentences** (maximum 1,400 characters) for executive summaries.
* **Citation Grounding Check:** Every bullet point must match a verified URL in the source list. Uncited claims are rejected.

---

## 11. Summary Governance Matrix

| Scenario / Decision Point | Platform Rule | Enforcement Mechanism |
| :--- | :--- | :--- |
| **Prospect Input Validation** | Limited to 250 catalog entities | `ProspectValidationGateway` deterministic resolver |
| **User Authentication** | Google OAuth 2.0 + Signed JWT | `authenticate_google_user` + `tokeninfo` verification |
| **User History Isolation** | Strictly partitioned per user | `WHERE user_id = current_user.id` SQL filtering |
| **External Web Research** | Real-time targeted Google searches | `Serper.dev API` collector + `Tavily` failover |
| **Identical Data from 2+ Sources** | Deduplicate value; list multi-citations | Value deduplication engine + Corroboration boost |
| **Tier 1 vs Tier 4 Conflict** | Tier 1 overrides Tier 4 | `AuthorityRanker` + Source tier weighting |
| **Tier 1 vs Tier 1 Conflict** | No silent discard; present dual attribution | `resolve_metric_conflicts` with transparency note |
| **Different Period Numbers** | Not a conflict; retain both by fiscal year | `extract_reporting_period` temporal grouping |
| **AI Output Synthesis** | Zero-hallucination grounded prompts | Underwriting Copilot Prompt System + Gemini AI |
| **Output Citations** | Every factual claim requires grounded source | `models/evidence.py` Evidence attribution contract |

