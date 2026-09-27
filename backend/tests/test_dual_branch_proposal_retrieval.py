"""
Test Dual-Branch Proposal Architecture:
1. Canonical Document & Authoritative Chunking
2. Dense + BM25 Retrieval per Catalog Parameter
3. Dual-Branch Parameter Evaluation Integration
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath("."))
from services.proposal_retrieval_service import (
    create_canonical_chunks,
    extract_chunks_from_profile,
    RFPChunkRetriever,
    retrieve_authoritative_catalog_excerpts
)
from services.proposal_parameter_service import (
    evaluate_all_parameters,
    clear_recommendation_cache,
    get_parameter_catalog
)
from config.proposal_analysis_config import (
    PROPOSAL_PARAMETERS_CATALOG,
    PROPOSAL_PARAMETERS_BY_ID
)


class TestDualBranchProposalRetrieval(unittest.TestCase):

    def setUp(self):
        clear_recommendation_cache()
        self.sample_rfp_text = """
--- Page 1 ---
COMMERCIAL INSURANCE RFP
1. EXECUTIVE OVERVIEW
The issuing authority seeks proposals for commercial property and casualty underwriting operations.
Target domain is Commercial Insurance.

--- Page 2 ---
2. FUNCTIONAL SCOPE & UNDERWRITING REQUIREMENTS
Vendor must provide an automated underwriting risk ingestion platform.
Loss ratio tolerance must be monitored in real-time with combined ratio benchmarks under 88%.
Pricing discipline requires automated rating engine integration with actuarial tables.

--- Page 3 ---
3. CLAIMS ADJUDICATION SLA & DELIVERABLES
Claims intimation must be handled via digital FNOL portal.
Undisputed commercial claims turnaround time (TAT) must not exceed 5 business days.
Automated claims fraud detection algorithm must flag suspicious submissions before payout.

--- Page 4 ---
4. SECURITY AND REGULATORY COMPLIANCE
The vendor platform must achieve SOC 2 Type II compliance and ISO 27001 certification.
All policyholder telemetry must comply with statutory DPDP and GDPR data privacy regulations.
"""
        self.sample_profile = {
            "proposal_id": "RFP-DUAL-BRANCH-001",
            "proposal_title": "Commercial Property & Casualty Modernization RFP",
            "domain": "Commercial Insurance",
            "summary": "Commercial P&C modernization covering underwriting automation, fast claims adjudication, and SOC 2 security.",
            "canonical_text": self.sample_rfp_text,
            "business_objectives": [
                "Automate underwriting risk intake",
                "Reduce claims settlement turnaround to 5 days"
            ],
            "functional_requirements": [
                "Automated underwriting risk intake with combined ratio tracking",
                "Digital FNOL claims intimation and fraud detection",
                "SOC 2 Type II and ISO 27001 security compliance"
            ]
        }

    def test_01_canonical_chunking_with_page_preservation(self):
        """Verify chunks preserve page numbers and section headers across pages."""
        chunks = create_canonical_chunks(self.sample_rfp_text, chunk_size=500, overlap=100)
        self.assertTrue(len(chunks) >= 4)
        
        pages = [c["page_number"] for c in chunks]
        self.assertIn(1, pages)
        self.assertIn(2, pages)
        self.assertIn(3, pages)
        self.assertIn(4, pages)

    def test_02_dense_and_bm25_retrieval_accuracy(self):
        """Verify parameters retrieve authoritative excerpts from the correct pages."""
        chunks = create_canonical_chunks(self.sample_rfp_text)
        results = retrieve_authoritative_catalog_excerpts(chunks)

        # Underwriting relevance should match page 2
        underwriting_res = results.get("underwriting_relevance")
        self.assertIsNotNone(underwriting_res)
        self.assertTrue(underwriting_res["score"] > 0)
        self.assertTrue(any("underwriting" in ex.lower() for ex in underwriting_res["excerpts"]))

        # Claims relevance should match page 3 with 5-day TAT quote
        claims_res = results.get("claims_relevance")
        self.assertIsNotNone(claims_res)
        self.assertTrue(claims_res["score"] > 0)
        self.assertTrue(any("claims" in ex.lower() or "tat" in ex.lower() for ex in claims_res["excerpts"]))

        # Regulatory / Compliance should match page 4
        reg_res = results.get("regulatory_compliance")
        self.assertIsNotNone(reg_res)
        self.assertTrue(reg_res["score"] > 0)
        self.assertTrue(any("compliance" in ex.lower() or "dpdp" in ex.lower() or "regulatory" in ex.lower() for ex in reg_res["excerpts"]))

    def test_03_dual_branch_evaluate_all_parameters(self):
        """Verify evaluate_all_parameters uses dual branch and populates all 15 catalog items."""
        mock_evaluations = [
            {
                "parameter_id": "underwriting_relevance",
                "parameter": "Underwriting Relevance",
                "relevance_score": 95,
                "recommendation": "recommended",
                "reason": "Directly mandated in section 2.",
                "rfp_evidence": ["[Page 2] Vendor must provide an automated underwriting risk ingestion platform."],
                "confidence": "High"
            },
            {
                "parameter_id": "claims_relevance",
                "parameter": "Claims Relevance",
                "relevance_score": 90,
                "recommendation": "recommended",
                "reason": "Explicit 5-day TAT SLA mandated in section 3.",
                "rfp_evidence": ["[Page 3] Undisputed commercial claims turnaround time (TAT) must not exceed 5 business days."],
                "confidence": "High"
            },
            {
                "parameter_id": "regulatory_compliance",
                "parameter": "Regulatory / Compliance Fit",
                "relevance_score": 88,
                "recommendation": "recommended",
                "reason": "DPDP and statutory compliance required.",
                "rfp_evidence": ["[Page 4] All policyholder telemetry must comply with statutory DPDP and GDPR data privacy regulations."],
                "confidence": "High"
            },
            {
                "parameter_id": "business_alignment",
                "parameter": "Business Alignment",
                "relevance_score": 85,
                "recommendation": "recommended",
                "reason": "Fits Commercial lines.",
                "rfp_evidence": ["[Page 1] Target domain is Commercial Insurance."],
                "confidence": "High"
            },
            {
                "parameter_id": "digital_transformation",
                "parameter": "Digital Transformation",
                "relevance_score": 80,
                "recommendation": "recommended",
                "reason": "Digital intake modernization.",
                "rfp_evidence": [],
                "confidence": "High"
            }
        ]

        with patch("services.proposal_parameter_service.query_gemini") as mock_gemini:
            mock_gemini.return_value = {"parameter_evaluations": mock_evaluations}
            results = evaluate_all_parameters(self.sample_profile)

        self.assertEqual(len(results), 15)
        
        # Verify recommended parameters
        claims_eval = next(r for r in results if r["parameter_id"] == "claims_relevance")
        self.assertEqual(claims_eval["recommendation"], "recommended")
        self.assertEqual(claims_eval["relevance_score"], 90)
        self.assertTrue(len(claims_eval["rfp_evidence"]) > 0)
        self.assertIn("Page 3", claims_eval["rfp_evidence"][0])

        # Verify not recommended parameter has safe defaults
        other_eval = next(r for r in results if r["parameter_id"] not in [m["parameter_id"] for m in mock_evaluations])
        self.assertEqual(other_eval["recommendation"], "not_recommended")
        self.assertEqual(other_eval["relevance_score"], 15)

    def test_04_fallback_chunk_extraction_from_profile_without_raw_text(self):
        """Verify mock profiles lacking canonical_text still extract chunks from structured fields."""
        profile_no_text = {
            "proposal_title": "Cyber Risk Assessment RFP",
            "business_objectives": ["Identify corporate cyber vulnerabilities"],
            "functional_requirements": ["Penetration testing and continuous threat monitoring"]
        }
        chunks = extract_chunks_from_profile(profile_no_text)
        self.assertTrue(len(chunks) > 0)
        self.assertTrue(any("penetration testing" in c["text"].lower() for c in chunks))


if __name__ == "__main__":
    unittest.main()
