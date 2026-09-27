import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath("."))
from services.proposal_analysis_service import (
    get_parameter_specific_rfp_clauses,
    evaluate_parameter_fit,
    analyze_proposal_fit
)
from config.proposal_analysis_config import PROPOSAL_PARAMETERS_BY_ID
from models.user import User

class TestProposalAnalysisOptimization(unittest.TestCase):
    def setUp(self):
        self.mock_user = User(
            id=1,
            uuid="test-user-uuid-123",
            email="analyst@example.com",
            name="Underwriting Analyst"
        )
        self.mock_proposal_profile = {
            "proposal_id": "RFP-TEST-001",
            "proposal_title": "Enterprise Commercial Claims Modernization RFP",
            "domain": "Commercial Insurance",
            "filename": "Claims_RFP.pdf",
            "business_objectives": ["Automate claims adjudication", "Reduce loss adjustment ratio"],
            "functional_requirements": [
                "Claims SLA: Payout within 7 business days for undisputed commercial claims",
                "Automated FNOL intake with OCR document intelligence",
                "REST API integration with HRMS and broker portal",
                "Vendor must be ISO 27001 certified and SOC 2 Type II compliant",
                "Solvency ratio must exceed regulatory minimum of 1.50x"
            ],
            "requirements": [
                "Claims SLA: Payout within 7 business days for undisputed commercial claims",
                "Automated FNOL intake with OCR document intelligence"
            ]
        }

    def test_01_parameter_specific_context_slicing(self):
        """Verify context slicing extracts parameter-specific RFP clauses instead of generic top 5."""
        claims_meta = PROPOSAL_PARAMETERS_BY_ID["claims_relevance"]
        clauses = get_parameter_specific_rfp_clauses("claims_relevance", claims_meta, self.mock_proposal_profile)
        self.assertTrue(len(clauses) > 0)
        self.assertTrue(any("claims" in c.lower() for c in clauses))
        
        # Technology modernization parameter should match API/system requirements
        tech_meta = PROPOSAL_PARAMETERS_BY_ID["technology_modernization"]
        tech_clauses = get_parameter_specific_rfp_clauses("technology_modernization", tech_meta, self.mock_proposal_profile)
        self.assertTrue(any("api" in c.lower() or "portal" in c.lower() for c in tech_clauses))

    def test_02_mock_mode_5_tier_schema(self):
        """Verify 5-tier output schema in mock mode contains compliance_status, verified_capabilities, etc."""
        res = evaluate_parameter_fit(
            prospect_name="SBI Life Insurance",
            parameter_id="claims_relevance",
            proposal_profile=self.mock_proposal_profile,
            mock_mode=True
        )
        self.assertIn("compliance_status", res)
        self.assertIn("verified_capabilities", res)
        self.assertIn("rfp_line_item_matching", res)
        self.assertIn("producer_discovery_action", res)
        self.assertIn("gaps", res)
        self.assertEqual(res["fit_level"], "High")

    @patch("services.proposal_analysis_service.query_gemini")
    @patch("services.proposal_analysis_service.search_all_sources")
    def test_03_batched_proposal_analysis_execution(self, mock_search, mock_gemini):
        """Verify analyze_proposal_fit executes in batched mode and formats complete dossier."""
        from models.evidence import Evidence
        mock_search.return_value = [
            Evidence(
                parameter="Claims Relevance",
                title="SBI Life Annual Disclosures",
                content="SBI Life settlement ratio stands at 98.2% with fast turnaround.",
                source_url="https://sbilife.co.in/claims-statutory",
                source_name="SBI Life Disclosures",
                source_type="official"
            )
        ]
        mock_db = MagicMock()
        mock_gemini.return_value = {
            "parameter_evaluations": {
                "claims_relevance": {
                    "fit_level": "High",
                    "confidence": "High",
                    "compliance_status": "Full Compliance",
                    "summary": "SBI Life maintains an audited 98.2% claims settlement turnaround ratio.",
                    "reasoning": "Directly satisfies RFP 7-day claims turnaround SLA benchmark.",
                    "verified_capabilities": ["98.2% settlement ratio", "Digital FNOL portal"],
                    "rfp_line_item_matching": [
                        {
                            "rfp_requirement": "Claims payout within 7 business days",
                            "prospect_capability": "Average turnaround is 5.2 business days",
                            "alignment": "Full Fit"
                        }
                    ],
                    "gaps": ["1% delayed payout penalty waiver requires confirmation"],
                    "producer_discovery_action": "Request underwriting endorsement on penalty clause"
                }
            }
        }

        output = analyze_proposal_fit(
            db=mock_db,
            current_user=self.mock_user,
            prospect_id="INS-0001",
            prospect_name="SBI Life Insurance",
            proposal_profile=self.mock_proposal_profile,
            selected_parameters=["claims_relevance"],
            mock_mode=False
        )

        self.assertIn("parameter_analysis", output)
        self.assertEqual(len(output["parameter_analysis"]), 1)
        param_eval = output["parameter_analysis"][0]
        self.assertEqual(param_eval["compliance_status"], "Full Compliance")
        self.assertEqual(param_eval["fit_level"], "High")
        self.assertEqual(len(param_eval["rfp_line_item_matching"]), 1)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_04_parameter_validation_audit_logging(self):
        """Verify validate_selected_parameters logs audit details and preserves all valid selected parameters."""
        from services.proposal_parameter_service import validate_selected_parameters
        
        # Test 10 parameters
        selected_10 = [
            "business_alignment", "insurance_product_alignment", "underwriting_relevance",
            "claims_relevance", "ai_ml_adoption", "digital_transformation",
            "technology_modernization", "data_analytics", "financial_capacity", "growth_expansion"
        ]
        validated = validate_selected_parameters(selected_10)
        self.assertEqual(len(validated), 10)
        self.assertEqual(validated, selected_10)

        # Test subset with invalid parameter - invalid removed, valid preserved
        mixed = selected_10 + ["invalid_nonexistent_param"]
        validated_mixed = validate_selected_parameters(mixed)
        self.assertEqual(len(validated_mixed), 10)
        self.assertNotIn("invalid_nonexistent_param", validated_mixed)

    def test_05_streaming_proposal_analysis_sse_lifecycle(self):
        """Verify stream_proposal_analysis yields init, param_started, param_completed, summary_ready, complete."""
        from services.proposal_analysis_service import stream_proposal_analysis
        import json

        mock_db = MagicMock()
        selected_params = ["business_alignment", "claims_relevance", "ai_ml_adoption"]

        events = list(stream_proposal_analysis(
            db=mock_db,
            current_user=self.mock_user,
            prospect_id="INS-0001",
            prospect_name="SBI Life Insurance",
            proposal_profile=self.mock_proposal_profile,
            selected_parameters=selected_params,
            mock_mode=True
        ))

        self.assertTrue(len(events) >= 5)

        # Parse SSE events
        parsed_events = []
        for raw_event in events:
            lines = raw_event.strip().split("\n")
            event_type = None
            data = None
            for line in lines:
                if line.startswith("event: "):
                    event_type = line[7:].strip()
                elif line.startswith("data: "):
                    data = json.loads(line[6:].strip())
            if event_type and data:
                parsed_events.append((event_type, data))

        event_types = [e[0] for e in parsed_events]

        # 1. First event must be init
        self.assertEqual(event_types[0], "init")
        self.assertEqual(parsed_events[0][1]["total_parameters"], 3)

        # 2. param_started must be emitted for each parameter
        started_events = [e for e in parsed_events if e[0] == "param_started"]
        self.assertEqual(len(started_events), 3)
        started_pids = {e[1]["parameter_id"] for e in started_events}
        self.assertEqual(started_pids, set(selected_params))

        # 3. param_completed must be emitted for each completed parameter
        completed_events = [e for e in parsed_events if e[0] == "param_completed"]
        self.assertEqual(len(completed_events), 3)
        for ce in completed_events:
            self.assertEqual(ce[1]["status"], "completed")
            self.assertIn("fit_level", ce[1])
            self.assertIn("timestamp", ce[1])

        # 4. summary_ready must be emitted
        self.assertIn("summary_ready", event_types)
        summary_event = next(e for e in parsed_events if e[0] == "summary_ready")
        self.assertIn("executive_summary", summary_event[1])

        # 5. complete event must be emitted at the end
        self.assertEqual(event_types[-1], "complete")
        complete_event = parsed_events[-1]
        self.assertEqual(complete_event[1]["status"], "completed")
        self.assertIn("analysis_id", complete_event[1])
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_06_streaming_parameter_failure_tolerance(self):
        """Verify that a single parameter failure yields param_failed and does not terminate remaining parameters."""
        from services.proposal_analysis_service import stream_proposal_analysis
        import json

        mock_db = MagicMock()
        selected_params = ["claims_relevance", "ai_ml_adoption"]

        with patch("services.proposal_analysis_service.evaluate_parameter_fit") as mock_eval:
            def side_effect(prospect_name, parameter_id, proposal_profile, mock_mode):
                if parameter_id == "claims_relevance":
                    raise RuntimeError("Simulated API rate limit error on claims")
                return {
                    "parameter_id": parameter_id,
                    "parameter": "AI / ML Adoption",
                    "category": "Technology",
                    "fit_level": "High",
                    "confidence": "High",
                    "compliance_status": "Full Compliance",
                    "summary": "AI capabilities verified.",
                    "finding": "AI capabilities verified.",
                    "reasoning": "AI adopted.",
                    "verified_capabilities": ["ML models in production"],
                    "rfp_line_item_matching": [],
                    "evidence": [],
                    "sources": [],
                    "gaps": [],
                    "producer_discovery_action": "None"
                }
            mock_eval.side_effect = side_effect

            events = list(stream_proposal_analysis(
                db=mock_db,
                current_user=self.mock_user,
                prospect_id="INS-0001",
                prospect_name="SBI Life Insurance",
                proposal_profile=self.mock_proposal_profile,
                selected_parameters=selected_params,
                mock_mode=False
            ))

            parsed_events = []
            for raw_event in events:
                lines = raw_event.strip().split("\n")
                event_type = None
                data = None
                for line in lines:
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: "):
                        data = json.loads(line[6:].strip())
                if event_type and data:
                    parsed_events.append((event_type, data))

            event_types = [e[0] for e in parsed_events]
            self.assertIn("param_failed", event_types)
            self.assertIn("param_completed", event_types)
            self.assertIn("summary_ready", event_types)
            self.assertIn("complete", event_types)

            failed_event = next(e for e in parsed_events if e[0] == "param_failed")
            self.assertEqual(failed_event[1]["parameter_id"], "claims_relevance")
            self.assertIn("Simulated API rate limit", failed_event[1]["error"])

    def test_07_parameter_recommendation_resilience(self):
        """Verify evaluate_all_parameters gracefully handles various LLM JSON outputs and deterministic fallback."""
        from services.proposal_parameter_service import (
            evaluate_all_parameters,
            clear_recommendation_cache,
            _extract_evaluations_list
        )

        clear_recommendation_cache()

        # 1. Test _extract_evaluations_list with different formats
        # Format A: Dict with "parameter_evaluations"
        res_a = _extract_evaluations_list({
            "parameter_evaluations": [{"parameter_id": "claims_relevance", "relevance_score": 90}]
        })
        self.assertEqual(len(res_a), 1)

        # Format B: Direct list of dicts
        res_b = _extract_evaluations_list([
            {"parameter_id": "claims_relevance", "relevance_score": 90}
        ])
        self.assertEqual(len(res_b), 1)

        # Format C: Dict keyed by parameter ID
        res_c = _extract_evaluations_list({
            "claims_relevance": {"relevance_score": 90},
            "underwriting_relevance": {"relevance_score": 85},
            "ai_ml_adoption": {"relevance_score": 80},
            "digital_transformation": {"relevance_score": 75},
            "business_alignment": {"relevance_score": 70}
        })
        self.assertEqual(len(res_c), 5)

        # 2. Test explicit RuntimeError when both Gemini and Ollama fail
        with patch("services.proposal_parameter_service.query_gemini") as mock_gem, \
             patch("services.proposal_parameter_service.query_ollama") as mock_ollama:
            mock_gem.side_effect = RuntimeError("Gemini 503 unavailable")
            mock_ollama.side_effect = RuntimeError("Ollama connection refused")

            with self.assertRaises(RuntimeError) as ctx:
                evaluate_all_parameters(self.mock_proposal_profile)
            self.assertIn("AI services (Gemini/Ollama) are currently unavailable", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()


