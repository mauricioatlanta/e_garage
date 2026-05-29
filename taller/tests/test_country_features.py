# -*- coding: utf-8 -*-
"""Tests para la capa central de feature flags por país."""

import pytest

from taller.config.feature_flags import DEFAULT_COUNTRY, get_country_features


class TestGetCountryFeatures:
    """Tests de get_country_features()."""

    def test_cl_returns_expected_features(self):
        features = get_country_features("CL")
        assert features["country"] == "CL"
        assert features["tax_label"] == "IVA"
        assert features["currency_code"] == "CLP"
        assert features["mileage_unit"] == "km"

    def test_us_returns_expected_features(self):
        features = get_country_features("US")
        assert features["country"] == "US"
        assert features["tax_label"] == "Sales Tax"
        assert features["currency_code"] == "USD"
        assert features["mileage_unit"] == "mi"

    def test_invalid_country_fallback_to_cl(self):
        features = get_country_features("XX")
        assert features["country"] == DEFAULT_COUNTRY
        assert features["tax_label"] == "IVA"
        assert features["currency_code"] == "CLP"

    def test_none_country_fallback_to_cl(self):
        features = get_country_features(None)
        assert features["country"] == DEFAULT_COUNTRY

    def test_empty_string_country_fallback_to_cl(self):
        features = get_country_features("")
        assert features["country"] == DEFAULT_COUNTRY

    def test_result_is_independent_copy(self):
        features = get_country_features("CL")
        features["tax_label"] = "mutated"
        features2 = get_country_features("CL")
        assert features2["tax_label"] == "IVA"

    def test_lowercase_country_normalized(self):
        features = get_country_features("us")
        assert features["country"] == "US"
        assert features["tax_label"] == "Sales Tax"


class TestEnsureUiConfigTaxAndCurrency:
    """Tests de _ensure_ui_config_tax_and_currency con country_features."""

    @pytest.fixture
    def mock_request(self):
        class R:
            path = "/cl/documentos/form/"
            company_country = None

        return R()

    def test_usa_no_tax_lines_generates_tax_lines(self, mock_request):
        from taller.documentos.views_migrated import _ensure_ui_config_tax_and_currency

        mock_request.path = "/us/documentos/form/"
        ui_config = {}
        ui_config = _ensure_ui_config_tax_and_currency(mock_request, ui_config, None)
        assert ui_config.get("tax_lines")
        assert any(t.get("label") == "Sales Tax" for t in ui_config["tax_lines"])

    def test_usa_no_currency_fills_usd(self, mock_request):
        from taller.documentos.views_migrated import _ensure_ui_config_tax_and_currency

        mock_request.path = "/us/documentos/form/"
        ui_config = {}
        ui_config = _ensure_ui_config_tax_and_currency(mock_request, ui_config, None)
        assert ui_config.get("currency_code") == "USD"
        assert ui_config.get("currency_symbol") == "$"

    def test_cl_no_tax_lines_generates_iva(self, mock_request):
        from taller.documentos.views_migrated import _ensure_ui_config_tax_and_currency

        ui_config = {}
        ui_config = _ensure_ui_config_tax_and_currency(mock_request, ui_config, None)
        assert ui_config.get("tax_lines")
        assert any(t.get("label") == "IVA" for t in ui_config["tax_lines"])

    def test_cl_no_currency_fills_clp(self, mock_request):
        from taller.documentos.views_migrated import _ensure_ui_config_tax_and_currency

        ui_config = {}
        ui_config = _ensure_ui_config_tax_and_currency(mock_request, ui_config, None)
        assert ui_config.get("currency_code") == "CLP"
        assert ui_config.get("currency_symbol") == "$"

    def test_us_replaces_previous_tax_lines_no_mixing(self, mock_request):
        """En /us/... tax_lines debe ser solo Sales Tax, aunque ui_config traiga IVA."""
        from taller.documentos.views_migrated import _ensure_ui_config_tax_and_currency

        mock_request.path = "/us/documentos/form/"
        ui_config = {
            "tax_lines": [
                {"id": "iva", "label": "IVA", "rate": "19", "applies_to": "repuestos"},
            ],
        }
        ui_config = _ensure_ui_config_tax_and_currency(mock_request, ui_config, None)
        labels = [t.get("label") for t in ui_config.get("tax_lines", [])]
        assert "Sales Tax" in labels
        assert "IVA" not in labels

    def test_cl_replaces_previous_tax_lines_no_mixing(self, mock_request):
        """En /cl/... tax_lines debe ser solo IVA, aunque ui_config traiga Sales Tax."""
        from taller.documentos.views_migrated import _ensure_ui_config_tax_and_currency

        ui_config = {
            "tax_lines": [
                {"id": "sales_tax", "label": "Sales Tax", "rate": "8", "applies_to": "repuestos"},
            ],
        }
        ui_config = _ensure_ui_config_tax_and_currency(mock_request, ui_config, None)
        labels = [t.get("label") for t in ui_config.get("tax_lines", [])]
        assert "IVA" in labels
        assert "Sales Tax" not in labels
