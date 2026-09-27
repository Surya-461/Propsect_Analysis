import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath("."))
from models.evidence import Evidence
from config.research_parameters import (
    ResearchIntent,
    build_research_intents
)
from research.source_manager import is_relevant_evidence
from research.search_router import route_and_execute_research

class TestQueryEngineOptimization(unittest.TestCase):
    def setUp(self):
        self.company = "SBI Life Insurance"

    def test_01_solvency_query_and_domain_filtering(self):
        """Test 1: Verify Solvency Ratio intent, Serper Google syntax, Tavily NLP, and domain filters."""
        intents = build_research_intents(self.company, "Financial Strength")
        solvency_intent = next((i for i in intents if i.metric == "Solvency Ratio"), None)
        self.assertIsNotNone(solvency_intent)
        expected_serper = '"SBI Life Insurance" ("solvency ratio" OR "solvency margin") (site:irdai.gov.in OR site:crisil.com OR site:icra.in)'
        self.assertEqual(solvency_intent.serper_query, expected_serper)
        expected_tavily = "What is the solvency ratio or solvency margin of SBI Life Insurance, and what does it indicate about the company financial strength?"
        self.assertEqual(solvency_intent.tavily_query, expected_tavily)
        self.assertEqual(solvency_intent.domains, ["irdai.gov.in", "crisil.com", "icra.in"])

    def test_02_aum_focused_query(self):
        """Test 2: Verify AUM query is focused and distinct from general queries."""
        intents = build_research_intents(self.company, "Company Scale")
        aum_intent = next((i for i in intents if i.metric == "AUM"), None)
        self.assertIsNotNone(aum_intent)
        self.assertEqual(aum_intent.serper_query, '"SBI Life Insurance" AUM "assets under management"')
        self.assertIn("assets under management", aum_intent.tavily_query.lower())

    def test_03_workforce_focused_query(self):
        """Test 3: Verify Workforce query is focused and separated from financial scale."""
        intents = build_research_intents(self.company, "Company Scale")
        workforce_intent = next((i for i in intents if i.metric == "Workforce"), None)
        self.assertIsNotNone(workforce_intent)
        self.assertEqual(workforce_intent.serper_query, '"SBI Life Insurance" (employees OR workforce OR headcount)')
        self.assertIn("workforce", workforce_intent.tavily_query.lower())

    def test_04_numeric_table_preservation(self):
        """Test 4: Verify financial numeric table data is PRESERVED and not discarded."""
        sample_financial_text = "Revenue 2025: 12,450 crore Total Assets: 1,20,000 crore Solvency Ratio: 2.18 Premium: 54,000 crore PAT: 2,100 crore"
        ev = Evidence(
            parameter="Financial Strength",
            title="SBI Life Annual Financial Results",
            content=sample_financial_text,
            source_url="https://sbilife.co.in/results",
            source_name="SBI Life",
            source_type="official"
        )
        self.assertTrue(is_relevant_evidence(self.company, ev), "Financial numeric table must NOT be removed")

    def test_05_irrelevant_numeric_noise_filtering(self):
        """Test 5: Verify non-financial page-number and navigation noise is filtered."""
        sample_noise_text = "SBI Life Insurance Page 1 2 3 4 5 6 7 8 9 10 Next Previous"
        ev = Evidence(
            parameter="Company Scale",
            title="Pagination Index",
            content=sample_noise_text,
            source_url="https://sbilife.co.in/page-list",
            source_name="SBI Life Index",
            source_type="general_web"
        )
        self.assertFalse(is_relevant_evidence(self.company, ev), "Page number / navigation noise must be filtered")

    @patch("research.search_router.collect_financial_evidence", return_value=[])
    @patch("research.search_router.collect_google_news_evidence", return_value=[])
    def test_06_api_failure_and_fallback(self, mock_news, mock_fin):
        """Test 6: Verify pipeline handles provider failures gracefully and falls back."""
        with patch("research.search_router.collect_tavily_evidence", return_value=[]):
            with patch("research.search_router.collect_serper_evidence", side_effect=Exception("Serper Quota Exhausted")):
                evidence, conflicts = route_and_execute_research(
                    company_name=self.company,
                    parameter="Financial Strength",
                    max_queries=1
                )
                self.assertIsInstance(evidence, list)
                self.assertIsInstance(conflicts, list)

    @patch("research.search_router.collect_financial_evidence", return_value=[])
    @patch("research.search_router.collect_google_news_evidence", return_value=[])
    def test_07_query_deduplication(self, mock_news, mock_fin):
        """Test 7: Verify duplicate queries are deduplicated."""
        duplicate_intent = ResearchIntent(
            company=self.company,
            parameter="Financial Strength",
            metric="Solvency Ratio",
            query_type="regulatory",
            serper_query='"SBI Life Insurance" ("solvency ratio" OR "solvency margin") (site:irdai.gov.in)',
            tavily_query="What is the solvency ratio of SBI Life Insurance?"
        )
        with patch("research.search_router.collect_tavily_evidence", return_value=[]) as mock_tavily:
            with patch("research.search_router.collect_serper_evidence", return_value=[]) as mock_serper:
                route_and_execute_research(
                    company_name=self.company,
                    parameter="Financial Strength",
                    research_intents=[duplicate_intent, duplicate_intent],
                    max_queries=2
                )
                self.assertEqual(mock_tavily.call_count, 1)
                self.assertEqual(mock_serper.call_count, 1)

    def test_08_traceability_metadata(self):
        """Test 8: Verify Evidence retains full traceability metadata."""
        from research.collectors.serper_search import collect_serper_evidence
        mock_serper_response = MagicMock()
        mock_serper_response.status = 200
        mock_serper_response.read.return_value = b'{"organic": [{"title": "SBI Life Solvency Report", "link": "https://irdai.gov.in/sbi", "snippet": "Solvency ratio of SBI Life is 2.18 for FY2025"}]}'
        
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_serper_response
        
        with patch("urllib.request.urlopen", return_value=mock_cm):
            with patch.dict(os.environ, {"SERPER_API_KEY": "fake_test_key"}):
                items = collect_serper_evidence(
                    query="test query",
                    parameter="Financial Strength",
                    prospect_name="SBI Life Insurance",
                    metric="Solvency Ratio",
                    query_type="regulatory"
                )
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0].metric, "Solvency Ratio")
                self.assertEqual(items[0].query_type, "regulatory")
                self.assertEqual(items[0].search_query, "test query")
                self.assertEqual(items[0].provider, "serper")

if __name__ == "__main__":
    unittest.main()
