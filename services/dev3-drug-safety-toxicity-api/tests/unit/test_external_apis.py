"""
Unit tests for external API clients.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.external_apis.drugbank_api import check_drug_interaction, _map_severity


class TestDrugBankAPI:
    """Test suite for DrugBank DDI client."""

    def test_map_severity_valid_strings(self):
        """Test severity mapping for all severity levels."""
        assert _map_severity("contraindicated") == 4
        assert _map_severity("major") == 3
        assert _map_severity("moderate") == 2
        assert _map_severity("minor") == 1
        assert _map_severity("unknown") == 0

    def test_map_severity_case_insensitive(self):
        """Test severity mapping is case-insensitive."""
        assert _map_severity("MAJOR") == 3
        assert _map_severity("Moderate") == 2
        assert _map_severity("CONTRAINDICATED") == 4

    def test_map_severity_none(self):
        """Test severity mapping handles None."""
        assert _map_severity(None) == 0

    @pytest.mark.asyncio
    async def test_check_ddi_known_interaction(self):
        """Test DDI check returns known interaction."""
        with patch("src.external_apis.drugbank_api.cache_get") as mock_cache_get:
            mock_cache_get.return_value = None  # Not in cache

            with patch("src.external_apis.drugbank_api.cache_set") as mock_cache_set:
                result = await check_drug_interaction("warfarin", "aspirin")

                assert result["interaction_found"] is True
                assert result["severity"] == "Major"
                assert "bleeding" in result["description"].lower()
                mock_cache_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_ddi_from_cache(self):
        """Test DDI check returns cached result."""
        cached_result = {
            "drug_a": "warfarin",
            "drug_b": "aspirin",
            "interaction_found": True,
        }

        with patch("src.external_apis.drugbank_api.cache_get") as mock_cache_get:
            mock_cache_get.return_value = cached_result

            result = await check_drug_interaction("warfarin", "aspirin")
            assert result == cached_result
            mock_cache_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_ddi_unknown_interaction(self):
        """Test DDI check for unknown drug pair."""
        with patch("src.external_apis.drugbank_api.cache_get") as mock_cache_get:
            mock_cache_get.return_value = None

            with patch("src.external_apis.drugbank_api.cache_set") as mock_cache_set:
                result = await check_drug_interaction("unknown_drug_a", "unknown_drug_b")

                assert result["interaction_found"] is False
                assert result["severity"] is None
                mock_cache_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_ddi_order_independent(self):
        """Test DDI check is order-independent."""
        with patch("src.external_apis.drugbank_api.cache_get") as mock_cache_get:
            mock_cache_get.return_value = None

            with patch("src.external_apis.drugbank_api.cache_set"):
                result1 = await check_drug_interaction("warfarin", "aspirin")
                result2 = await check_drug_interaction("aspirin", "warfarin")

                # Both should find the same interaction
                assert result1["interaction_found"] == result2["interaction_found"]
                assert result1["severity"] == result2["severity"]


class TestPharmGKBAPI:
    """Test suite for PharmGKB client."""

    @pytest.mark.asyncio
    async def test_get_pgx_recommendation_from_cache(self):
        """Test PGx lookup returns cached result."""
        from src.external_apis.pharmgkb_api import get_pgx_recommendation

        cached_result = {
            "gene": "CYP2C9",
            "drug": "warfarin",
            "recommendation": "Cached result",
        }

        with patch("src.external_apis.pharmgkb_api.cache_get") as mock_cache_get:
            mock_cache_get.return_value = cached_result

            result = await get_pgx_recommendation("CYP2C9", "warfarin")
            assert result == cached_result

    @pytest.mark.asyncio
    async def test_get_pgx_recommendation_fallback(self):
        """Test PGx lookup returns fallback when API unavailable."""
        from src.external_apis.pharmgkb_api import get_pgx_recommendation

        with patch("src.external_apis.pharmgkb_api.cache_get") as mock_cache_get:
            mock_cache_get.return_value = None

            with patch("src.external_apis.pharmgkb_api.cache_set"):
                with patch("src.external_apis.pharmgkb_api.httpx.AsyncClient") as mock_client:
                    # Simulate API failure
                    mock_async_client = AsyncMock()
                    mock_async_client.__aenter__.return_value = mock_async_client
                    mock_async_client.get.side_effect = Exception("Connection error")
                    mock_client.return_value = mock_async_client

                    result = await get_pgx_recommendation("CYP2C9", "unknown_drug")

                    # Should return fallback response
                    assert "recommendation" in result
                    assert result["source"] == "fallback"


class TestFAERSAPI:
    """Test suite for FAERS API client."""

    @pytest.mark.asyncio
    async def test_get_adverse_events_valid_response(self):
        """Test FAERS API returns valid response structure."""
        from src.external_apis.faers_api import get_adverse_events

        mock_response_data = {
            "meta": {"results": {"total": 100}},
            "results": [
                {
                    "safetyreportid": "12345",
                    "receiptdate": "2024-01-15",
                    "serious": 1,
                    "patient": {
                        "drug": [{"medicinalproduct": "aspirin"}],
                        "reaction": [{"reactionmeddrapt": "Gastrointestinal hemorrhage"}],
                    },
                }
            ],
        }

        with patch("src.external_apis.faers_api.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value = mock_async_client

            result = await get_adverse_events("aspirin", limit=10)

            assert result["drug"] == "aspirin"
            assert result["total_results"] == 100
            assert len(result["events"]) > 0
            assert "report_id" in result["events"][0]
