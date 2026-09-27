# Unified Insurance Prospect & Proposal Analysis Platform
## End-to-End Pseudocode Algorithm & Functional Specification

---

### Key Architectural Invariants

1. **Deterministic Precedence**: Prospect catalog lookup (`INS-0001` to `INS-0250`), regex requirement extractions, and the 6-archetype compatibility matrix execute **BEFORE** any search or AI analysis.
2. **Grounded Empirical Facts**: AI analyzes only validated disclosures; AI **never** invents carriers, sums insured, premiums, capabilities, or ratings.
3. **Hard Eligibility Constraints**: AI cannot override a deterministic license or compatibility failure (e.g., a pure Life carrier bidding on Property risk is strictly flagged as `LOW` compatibility).
4. **Traceable Citations**: Every finding, strength, gap, and risk is traceable to a source URL or explicit RFP document clause.
5. **Zero Numerical Scoring**: In accordance with product policy, all prospect-fit and proposal-fit numerical scores are set to `NULL`. The platform produces 100% qualitative, evidence-backed underwriting intelligence.
6. **Multi-Tier Resilient Fallback**: Cloud LLM (Gemini Flash) -> Local LLM (Ollama) -> Deterministic Rule-Based Fallback ensures zero platform downtime.

---

## 1. Step-by-Step Execution Algorithm

```text
ALGORITHM: Unified_Insurance_Prospect_and_Proposal_Platform
INPUT: User Request (Prospect Name, Mode: [STANDALONE_PROSPECT | PROPOSAL_BASED], Optional Proposal File/Text, Selected Parameters)
OUTPUT: Qualitative, Evidence-Backed Underwriting Intelligence Dossier

================================================================================
PHASE A: COMMON INGESTION & DETERMINISTIC VALIDATION GATE
================================================================================
STEP 1: USER AUTHENTICATION & INPUT SANITIZATION
  - Verify user session and extract UUID for multi-tenant data isolation.
  - Clean conversational prefixes and punctuation from input string.

STEP 2: CANONICAL PROSPECT RESOLUTION
  - Validate prospect against the 250-carrier universe (INS-0001 to INS-0250).
  - Match via: ID -> Exact Name -> Curated Alias -> Normalized Name -> Fuzzy Overlap.
  - IF carrier not found or ambiguous -> STOP and return error / candidate list.

STEP 3: BRANCH ON ANALYSIS MODE
  - IF Mode == "STANDALONE_PROSPECT":
      Execute Phase B (Case 1: General Prospect Intelligence).
  - IF Mode == "PROPOSAL_BASED":
      Execute Phase C (Case 2: Proposal / RFP Grounded Underwriting).

================================================================================
PHASE B: STANDALONE PROSPECT INTELLIGENCE (CASE 1)
================================================================================
STEP B1: RESEARCH ORCHESTRATION
  - Query official filings, IRDAI/NAIC statutory disclosures, rating agencies, and Tavily search across 8 core underwriting parameters (Scale, Solvency, Claims, Performance, etc.).
  - Stop if no verifiable disclosures exist.

STEP B2: TWO-TIER AI PROSPECT SYNTHESIS
  - Synthesize parameter summaries, exposures, and executive summary.
  - Primary: Google Gemini -> Fallback: Local Ollama -> Safety Net: Deterministic Synthesis.

STEP B3: PROSPECT METRICS SCORECARD & VERDICT
  - Extract factual ratios (e.g. Solvency Margin, Combined Ratio, Ratings) without inventing numbers.
  - Generate Underwriting Verdict (Risk Level: Low/Medium/High, Primary Exposure Classes).
  - Proceed to Phase D.

================================================================================
PHASE C: PROPOSAL / RFP GROUNDED UNDERWRITING ANALYSIS (CASE 2)
================================================================================
STEP C1: PROPOSAL DOCUMENT EXTRACTION
  - Read uploaded PDF/DOCX/TXT file or pasted text.
  - Deterministically extract: Sums Insured, Premiums, Deductibles, Underwriting Conditions Precedent, Exclusions.
  - Extract dynamic RFP-specific parameters (tagged 'Proposal-derived').

STEP C2: DETERMINISTIC COMPATIBILITY MATRIX (BEFORE AI)
  - Classify Carrier Archetype vs Proposal Line of Business.
  - Evaluate statutory compatibility: HIGH | MEDIUM | LOW.
  - Hard constraint: If carrier license legally bars the requested line (e.g., Life carrier bidding on Property) -> Enforce LOW compatibility before AI analysis.

STEP C3: TARGETED CREDIT-EFFICIENT RESEARCH
  - Run public research ONLY for parameters selected by the user (Recommended + Dynamic).
  - Group queries by shared source domains to minimize external API/web crawl credits.

STEP C4: PARAMETER FIT EVALUATION & EVIDENCE CLASSIFICATION
  - Classify evidence authority: CONFIRMED | SUPPORTED | INFERRED | UNKNOWN.
  - Assess qualitative alignment: FIT | PARTIAL FIT | GAP | UNKNOWN.
  - Identify Key Strengths, Key Gaps, Risks, and Producer Action Plan.
  - Proceed to Phase D.

================================================================================
PHASE D: COMMON GUARDRAILS, PERSISTENCE & COPILOT CONTEXT
================================================================================
STEP 4: OUTPUT GUARDRAILS & ZERO-SCORING ENFORCEMENT
  - Set all numerical fit scores to NULL (Qualitative compliance).
  - Clean markdown artifacts, table dumps, and HTML noise.
  - Cap sources and facts to a maximum of 5 items per parameter.

STEP 5: DATABASE PERSISTENCE (POSTGRESQL)
  - Persist complete analysis linked to `user_uuid`.

STEP 6: INTERACTIVE COPILOT CHAT READY
  - Initialize chat session grounded strictly in the active dossier disclosures.
  - Return final dossier to frontend UI.
```

---

## 2. Functional Definitions

```python
# ==============================================================================
# 1. COMMON VALIDATION & DISPATCH GATEWAY
# ==============================================================================

FUNCTION RUN_UNIFIED_ANALYSIS(request, current_user, db_session):
    user_uuid = current_user.uuid
    
    prospect, candidates, status = RESOLVE_PROSPECT(request.prospect_name)
    IF status != "MATCHED":
        RETURN GENERATE_RESOLUTION_ERROR(status, candidates)

    IF request.analysis_mode == "STANDALONE_PROSPECT":
        dossier = EXECUTE_PROSPECT_INTELLIGENCE_FLOW(prospect, request.parameters)
    ELSE:
        dossier = EXECUTE_PROPOSAL_UNDERWRITING_FLOW(prospect, request.proposal_input, request.selected_parameters)

    sanitized_dossier = APPLY_OUTPUT_GUARDRAILS(dossier)
    persisted_record  = PERSIST_DOSSIER_TO_DB(sanitized_dossier, user_uuid, db_session)
    
    RETURN persisted_record


FUNCTION RESOLVE_PROSPECT(raw_query):
    cleaned = CLEAN_STRING(raw_query)
    IF IS_CANONICAL_ID(cleaned):
        RETURN (GET_CATALOG_ITEM_BY_ID(cleaned), [GET_CATALOG_ITEM_BY_ID(cleaned)], "MATCHED")
    IF IS_EXACT_CATALOG_NAME(cleaned):
        RETURN (GET_CATALOG_ITEM_BY_NAME(cleaned), [GET_CATALOG_ITEM_BY_NAME(cleaned)], "MATCHED")
    IF cleaned IN KNOWN_ALIASES:
        target = KNOWN_ALIASES[cleaned]
        RETURN (GET_CATALOG_ITEM_BY_NAME(target), [GET_CATALOG_ITEM_BY_NAME(target)], "MATCHED")
    candidates = SEARCH_CATALOG_TOKEN_OVERLAP(cleaned)
    IF LENGTH(candidates) == 1:
        RETURN (candidates[0], candidates, "MATCHED")
    IF LENGTH(candidates) > 1:
        RETURN (NULL, candidates, "MULTIPLE_MATCHES")
    RETURN (NULL, [], "NOT_FOUND")


# ==============================================================================
# 2. CASE 1: STANDALONE PROSPECT INTELLIGENCE FUNCTIONS
# ==============================================================================

FUNCTION EXECUTE_PROSPECT_INTELLIGENCE_FLOW(prospect, requested_parameters):
    evidence_by_param = SEARCH_PUBLIC_DISCLOSURES_ACROSS_CORE_TAXONOMY(
        prospect.name, 
        parameters=requested_parameters OR DEFAULT_8_CORE_PARAMETERS
    )
    IF NO_EVIDENCE_FOUND(evidence_by_param):
        RETURN GENERATE_INSUFFICIENT_DATA_DOSSIER(prospect.name)

    ai_result = SYNTHESIZE_AI_WITH_FALLBACK(
        company=prospect.name,
        context=evidence_by_param,
        prompt_type="PROSPECT_INTELLIGENCE"
    )

    scorecard = EXTRACT_FACTUAL_METRICS_SCORECARD(evidence_by_param)
    verdict   = EXTRACT_UNDERWRITING_VERDICT(ai_result)

    RETURN {
        "company_name": prospect.name,
        "analysis_mode": "STANDALONE_PROSPECT",
        "executive_summary": ai_result.executive_summary,
        "parameters": ai_result.parameters,
        "metrics_scorecard": scorecard,
        "underwriting_verdict": verdict,
        "critical_data_gaps": ai_result.critical_data_gaps
    }


# ==============================================================================
# 3. CASE 2: PROPOSAL / RFP UNDERWRITING FUNCTIONS
# ==============================================================================

FUNCTION EXECUTE_PROPOSAL_UNDERWRITING_FLOW(prospect, proposal_input, user_selected_params):
    raw_text = EXTRACT_TEXT_FROM_DOCUMENT(proposal_input.file, proposal_input.text)
    rfp_reqs = EXTRACT_PROPOSAL_REQUIREMENTS(raw_text)
    compatibility = EVALUATE_ARCHETYPE_COMPATIBILITY(prospect.name, raw_text)

    checklist = GENERATE_PROPOSAL_CHECKLIST(raw_text)
    selected_params = user_selected_params OR checklist.recommended_parameters

    evidence_by_param = EXECUTE_CREDIT_EFFICIENT_RESEARCH(prospect.name, selected_params)

    evaluated_params = []
    FOR EACH param IN selected_params:
        p_fit = EVALUATE_SINGLE_PARAMETER_FIT(
            param_name=param,
            prospect_name=prospect.name,
            requirement_text=rfp_reqs.GET(param, ""),
            evidence_list=evidence_by_param.GET(param, []),
            source_label="Proposal-derived" IF param IN checklist.dynamic_names ELSE "Master Checklist"
        )
        evaluated_params.APPEND(p_fit)

    ai_summary = SYNTHESIZE_AI_WITH_FALLBACK(
        company=prospect.name,
        context={"compatibility": compatibility, "parameters": evaluated_params},
        prompt_type="PROPOSAL_DOSSIER"
    )

    RETURN {
        "company_name": prospect.name,
        "proposal_name": proposal_input.filename OR "Uploaded Proposal Document",
        "analysis_mode": "PROPOSAL_BASED",
        "proposal_compatibility": compatibility.rating,
        "compatibility_reason": compatibility.reason,
        "executive_summary": ai_summary.executive_summary,
        "selected_parameters": evaluated_params,
        "key_strengths": EXTRACT_TOP_ITEMS(evaluated_params, assessment="FIT"),
        "key_gaps": EXTRACT_TOP_ITEMS(evaluated_params, assessment="GAP"),
        "key_risks": EXTRACT_TOP_ITEMS(evaluated_params, assessment="PARTIAL FIT"),
        "overall_proposal_fit": DERIVE_QUALITATIVE_FIT(compatibility.rating, evaluated_params),
        "producer_action_plan": GENERATE_PRODUCER_ACTION_PLAN(evaluated_params)
    }


# ==============================================================================
# 4. DETERMINISTIC COMPATIBILITY & FIT LOGIC
# ==============================================================================

FUNCTION EVALUATE_ARCHETYPE_COMPATIBILITY(prospect_name, proposal_text):
    carrier_archetype = CLASSIFY_CARRIER_ARCHETYPE(prospect_name)
    proposal_line     = CLASSIFY_PROPOSAL_LINE(proposal_text)

    IF carrier_archetype == "Composite":
        RETURN {"rating": "HIGH", "reason": "Composite carrier authorized across all lines."}

    IF carrier_archetype == "Reinsurance":
        IF "Reinsurance" IN proposal_line:
            RETURN {"rating": "HIGH", "reason": "Authorized treaty and facultative reinsurer."}
        RETURN {"rating": "LOW", "reason": "Professional reinsurers cannot underwrite direct retail RFP tenders."}

    IF carrier_archetype == "Life Insurance":
        IF "Life" IN proposal_line:
            RETURN {"rating": "HIGH", "reason": "Authorized for group term, life, and employee pensions."}
        RETURN {"rating": "LOW", "reason": "Statutory life license legally bars property, casualty, and cyber underwriting."}

    IF carrier_archetype == "Commercial P&C":
        IF "Commercial P&C" IN proposal_line OR "Health" IN proposal_line:
            RETURN {"rating": "HIGH", "reason": "Full non-life license permitting commercial and health underwriting."}
        RETURN {"rating": "LOW", "reason": "Non-life license is barred from underwriting pure life mortality plans."}

    RETURN {"rating": "MEDIUM", "reason": "Requires line-by-line review."}


FUNCTION EVALUATE_SINGLE_PARAMETER_FIT(param_name, prospect_name, requirement_text, evidence_list, source_label):
    valid_snippets = EXTRACT_CLEAN_SNIPPETS(evidence_list)
    
    IF IS_EMPTY(valid_snippets):
        RETURN {
            "parameter_name": param_name,
            "source": source_label,
            "proposal_requirement": requirement_text,
            "public_evidence": "No reliable public disclosures found in authoritative filings.",
            "evidence_classification": "UNKNOWN",
            "assessment": "UNKNOWN",
            "confidence": "LOW",
            "gap": "Public disclosures do not verify this parameter. Direct underwriter confirmation required.",
            "recommendation": "Request written confirmation during tender clarification.",
            "sources": []
        }

    classification = "CONFIRMED" IF HAS_STATUTORY_FILING(evidence_list) ELSE ("SUPPORTED" IF LENGTH(valid_snippets) >= 2 ELSE "INFERRED")
    
    evidence_str = JOIN(" ", valid_snippets).TO_LOWER()
    IF CONTAINS_KEYWORDS(evidence_str, ["licensed", "solvency", "capital", "network", "approved"]):
        assessment = "FIT"
        confidence = "HIGH"
        gap = "None identified from authoritative public filings."
    ELSE IF CONTAINS_KEYWORDS(evidence_str, ["partial", "limited", "restriction", "deficit"]):
        assessment = "PARTIAL FIT"
        confidence = "MEDIUM"
        gap = "Specific conditions require operational endorsement."
    ELSE:
        assessment = "FIT"
        confidence = "HIGH" IF classification != "INFERRED" ELSE "MEDIUM"
        gap = "No material gap detected."

    RETURN {
        "parameter_name": param_name,
        "source": source_label,
        "proposal_requirement": requirement_text,
        "public_evidence": LIMIT_SENTENCES(evidence_str, 3),
        "evidence_classification": classification,
        "assessment": assessment,
        "confidence": confidence,
        "gap": gap,
        "recommendation": "Incorporate standard SLA covenants in policy schedule.",
        "sources": EXTRACT_VALID_SOURCES(evidence_list, limit=5)
    }


# ==============================================================================
# 5. AI SYNTHESIS WITH MULTI-TIER FALLBACK
# ==============================================================================

FUNCTION SYNTHESIZE_AI_WITH_FALLBACK(company, context, prompt_type):
    prompt = COMPILE_GROUNDED_PROMPT(company, context, prompt_type)

    TRY:
        result = CALL_GEMINI(prompt)
        IF IS_VALID_JSON(result):
            RETURN result
    CATCH Exception AS e:
        LOG_WARNING("Gemini failed ({0}). Invoking Tier 2 Ollama...", e)

    TRY:
        result = CALL_OLLAMA(prompt, model="qwen2.5:1.5b")
        IF IS_VALID_JSON(result):
            RETURN result
    CATCH Exception AS e:
        LOG_WARNING("Ollama failed ({0}). Invoking Tier 3 Fallback...", e)

    RETURN GENERATE_DETERMINISTIC_SYNTHESIS(company, context)


# ==============================================================================
# 6. OUTPUT GUARDRAILS & DATABASE PERSISTENCE
# ==============================================================================

FUNCTION APPLY_OUTPUT_GUARDRAILS(dossier):
    dossier["score"] = NULL
    dossier["overall_score"] = NULL
    dossier["proposal_fit_score"] = NULL
    dossier["executive_summary"] = CLEAN_MARKDOWN_AND_NOISE(dossier["executive_summary"])

    FOR EACH item IN dossier.GET("selected_parameters", []) + dossier.GET("parameters", {}).VALUES():
        item["sources"] = item.GET("sources", [])[:5]
        item["key_facts"] = item.GET("key_facts", [])[:5]

    RETURN dossier


FUNCTION PERSIST_DOSSIER_TO_DB(dossier, user_uuid, db_session):
    TRY:
        record = DB_INSERT("analyses", {
            "user_uuid": user_uuid,
            "company_name": dossier["company_name"],
            "analysis_mode": dossier["analysis_mode"],
            "proposal_filename": dossier.GET("proposal_name", NULL),
            "risk_rating": dossier.GET("overall_proposal_fit", dossier.GET("underwriting_verdict", {}).GET("overall_risk_level", "Medium")),
            "executive_summary": dossier["executive_summary"],
            "report_data": dossier.GET("selected_parameters") OR dossier.GET("parameters"),
            "critical_data_gaps": dossier.GET("key_gaps") OR dossier.GET("critical_data_gaps"),
            "score": NULL,
            "created_at": GET_UTC_NOW()
        })
        db_session.COMMIT()
        dossier["id"] = record.id
    CATCH Exception AS exc:
        db_session.ROLLBACK()
        LOG_ERROR("DB persistence error: {0}", exc)
        dossier["id"] = NULL

    RETURN dossier
```
