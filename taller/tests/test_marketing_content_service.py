"""
Tests para MarketingContentService y sus colaboradores internos.

Cubre:
  - fallback cuando no hay API key
  - generación exitosa con AI mockeada
  - JSON inválido del proveedor → fallback
  - timeout → fallback
  - HTTP error → fallback
  - validación de slugify
  - contenido diferenciado por red social
  - ausencia de PII y secretos en el output
"""
import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from taller.services.marketing_content_service import (
    FORMAT_VERSION,
    MarketingAIError,
    MarketingAIProvider,
    MarketingContentService,
    MarketingFallback,
    MarketingPackage,
    slugify,
)

FEATURE      = "Briefing inteligente para desarmadurías"
DESCRIPCION  = "Panel que analiza indicadores del negocio y entrega alertas, resumen y recomendaciones"
FAKE_DATE    = date(2026, 8, 4)

# JSON válido que devolvería el API de Anthropic
_VALID_AI_RESPONSE = {
    "propuesta_valor": "Conoce tu negocio en segundos con el Briefing inteligente",
    "facebook": {
        "texto": (
            "¡Presentamos el Briefing inteligente para desarmadurías! "
            "Ahora puedes ver el resumen de tu negocio cada día sin perder tiempo. "
            "Pruébalo en egarage.cl"
        )
    },
    "instagram": {
        "texto": "⚡ Nuevo en eGarage\nBriefing inteligente\nTu negocio analizado al instante.\n👉 egarage.cl"
    },
    "tiktok": {
        "gancho": "¿Sigues revisando tu desarmaduria pantalla por pantalla?",
        "guion":  "Con el nuevo Briefing inteligente de eGarage, tienes el resumen de tu negocio al instante.",
        "texto_pantalla": ["TU DESARMADURIA", "EN UN VISTAZO", "egarage.cl"],
        "escenas": [
            "escena 1: manos abriendo el dashboard en celular",
            "escena 2: alertas y KPIs en pantalla",
            "escena 3: logo de eGarage",
        ],
        "cta": "Empieza gratis en egarage.cl",
    },
    "reel": {
        "escenas": [
            {"tiempo": "0-5s",  "texto": "¿Cómo va tu desarmaduria hoy?", "visual": "pantalla del dashboard"},
            {"tiempo": "5-12s", "texto": "Alertas en tiempo real",          "visual": "animación de alertas"},
            {"tiempo": "12-20s","texto": "Todo en un panel",                "visual": "vista general del briefing"},
            {"tiempo": "20-27s","texto": "egarage.cl",                      "visual": "logo eGarage"},
        ]
    },
    "historias": [
        {"pantalla": 1, "texto": "⚡ Nuevo en eGarage", "cta": False},
        {"pantalla": 2, "texto": "Briefing inteligente", "cta": False},
        {"pantalla": 3, "texto": "Tu negocio analizado al instante", "cta": False},
        {"pantalla": 4, "texto": "Alertas, KPIs y recomendaciones", "cta": False},
        {"pantalla": 5, "texto": "Pruébalo gratis en egarage.cl", "cta": True},
    ],
    "hashtags": ["eGarage", "TallerMecanico", "Desarmaduria", "GestionTaller", "SoftwareTaller"],
}


def _make_api_response(data: dict) -> MagicMock:
    """Crea un mock de requests.Response que retorna data como JSON de Anthropic."""
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": [{"text": json.dumps(data)}]
    }
    return mock_resp


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic_ascii(self):
        assert slugify("hello world") == "hello-world"

    def test_accents_stripped(self):
        assert slugify("Briefing inteligente") == "briefing-inteligente"

    def test_special_chars_removed(self):
        assert slugify("feature (v2)!") == "feature-v2"

    def test_max_length(self):
        long_text = "a" * 100
        assert len(slugify(long_text)) <= 50

    def test_empty_returns_default(self):
        assert slugify("") == "sin-nombre"

    def test_only_special_chars(self):
        assert slugify("!!!") == "sin-nombre"

    def test_spaces_become_dashes(self):
        assert slugify("hello   world") == "hello-world"


# ---------------------------------------------------------------------------
# MarketingFallback
# ---------------------------------------------------------------------------

class TestMarketingFallback:
    def _generate(self):
        return MarketingFallback.generate(FEATURE, DESCRIPCION, "Talleres CL", "CL")

    def test_returns_all_keys(self):
        data = self._generate()
        assert "propuesta_valor" in data
        assert "facebook" in data
        assert "instagram" in data
        assert "tiktok" in data
        assert "reel" in data
        assert "historias" in data
        assert "hashtags" in data

    def test_facebook_contains_url(self):
        data = self._generate()
        assert "egarage.cl" in data["facebook"]["texto"]

    def test_instagram_is_shorter_than_facebook(self):
        data = self._generate()
        assert len(data["instagram"]["texto"]) < len(data["facebook"]["texto"])

    def test_tiktok_has_required_keys(self):
        data = self._generate()
        tk = data["tiktok"]
        assert "gancho" in tk
        assert "guion" in tk
        assert "texto_pantalla" in tk
        assert "escenas" in tk
        assert "cta" in tk

    def test_historias_has_5_screens(self):
        data = self._generate()
        assert len(data["historias"]) == 5

    def test_last_historia_is_cta(self):
        data = self._generate()
        assert data["historias"][-1]["cta"] is True

    def test_hashtags_is_list(self):
        data = self._generate()
        assert isinstance(data["hashtags"], list)
        assert len(data["hashtags"]) >= 3

    def test_no_pii_in_output(self):
        import re
        data = self._generate()
        text = json.dumps(data)
        # RUT chileno
        assert not re.search(r"\d{2}\.\d{3}\.\d{3}-[\dkK]", text)
        # Teléfono
        assert not re.search(r"\+56\d{9}", text)

    def test_content_differs_per_network(self):
        data = self._generate()
        assert data["facebook"]["texto"] != data["instagram"]["texto"]
        assert data["instagram"]["texto"] != data["tiktok"]["guion"]


# ---------------------------------------------------------------------------
# MarketingContentService — sin API key
# ---------------------------------------------------------------------------

class TestServiceNoApiKey:

    @patch("taller.services.marketing_content_service.settings")
    def test_uses_fallback_without_key(self, mock_settings):
        mock_settings.ANTHROPIC_API_KEY = ""
        mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

        pkg = MarketingContentService.generate(
            feature=FEATURE,
            descripcion=DESCRIPCION,
            fecha=FAKE_DATE,
        )
        assert isinstance(pkg, MarketingPackage)
        assert pkg.fallback_used is True
        assert pkg.modelo == ""

    @patch("taller.services.marketing_content_service.settings")
    def test_package_has_correct_metadata(self, mock_settings):
        mock_settings.ANTHROPIC_API_KEY = ""
        pkg = MarketingContentService.generate(
            feature=FEATURE,
            descripcion=DESCRIPCION,
            fecha=FAKE_DATE,
        )
        assert pkg.feature == FEATURE
        assert pkg.fecha == FAKE_DATE
        assert pkg.idioma == "es"

    @patch("taller.services.marketing_content_service.settings")
    def test_to_dict_includes_formato_version(self, mock_settings):
        mock_settings.ANTHROPIC_API_KEY = ""
        pkg = MarketingContentService.generate(feature=FEATURE, descripcion=DESCRIPCION, fecha=FAKE_DATE)
        d = pkg.to_dict()
        assert d["formato_version"] == FORMAT_VERSION
        assert d["fallback_used"] is True
        assert "redes" in d

    def test_raises_on_empty_feature(self):
        with pytest.raises(ValueError, match="feature"):
            MarketingContentService.generate(feature="", descripcion=DESCRIPCION)

    def test_raises_on_empty_descripcion(self):
        with pytest.raises(ValueError, match="descripcion"):
            MarketingContentService.generate(feature=FEATURE, descripcion="")


# ---------------------------------------------------------------------------
# MarketingContentService — con AI mockeada
# ---------------------------------------------------------------------------

class TestServiceWithAI:

    @patch("taller.services.marketing_content_service._requests.post")
    @patch("taller.services.marketing_content_service.settings")
    def test_uses_ai_when_key_present(self, mock_settings, mock_post):
        mock_settings.ANTHROPIC_API_KEY = "sk-test-fake-key"
        mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
        mock_post.return_value = _make_api_response(_VALID_AI_RESPONSE)

        pkg = MarketingContentService.generate(
            feature=FEATURE,
            descripcion=DESCRIPCION,
            fecha=FAKE_DATE,
        )
        assert pkg.fallback_used is False
        assert pkg.modelo == "claude-haiku-4-5-20251001"

    @patch("taller.services.marketing_content_service._requests.post")
    @patch("taller.services.marketing_content_service.settings")
    def test_ai_content_passes_through(self, mock_settings, mock_post):
        mock_settings.ANTHROPIC_API_KEY = "sk-test-fake-key"
        mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
        mock_post.return_value = _make_api_response(_VALID_AI_RESPONSE)

        pkg = MarketingContentService.generate(feature=FEATURE, descripcion=DESCRIPCION, fecha=FAKE_DATE)
        assert pkg.propuesta_valor == _VALID_AI_RESPONSE["propuesta_valor"]
        assert pkg.facebook["texto"] == _VALID_AI_RESPONSE["facebook"]["texto"]

    @patch("taller.services.marketing_content_service._requests.post")
    @patch("taller.services.marketing_content_service.settings")
    def test_fallback_on_invalid_json(self, mock_settings, mock_post):
        mock_settings.ANTHROPIC_API_KEY = "sk-test-fake-key"
        mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
        bad_resp = MagicMock()
        bad_resp.ok = True
        bad_resp.json.return_value = {"content": [{"text": "ESTO NO ES JSON {{{"}]}
        mock_post.return_value = bad_resp

        pkg = MarketingContentService.generate(feature=FEATURE, descripcion=DESCRIPCION, fecha=FAKE_DATE)
        assert pkg.fallback_used is True

    @patch("taller.services.marketing_content_service._requests.post")
    @patch("taller.services.marketing_content_service.settings")
    def test_fallback_on_timeout(self, mock_settings, mock_post):
        import requests as req_lib
        mock_settings.ANTHROPIC_API_KEY = "sk-test-fake-key"
        mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
        mock_post.side_effect = req_lib.exceptions.Timeout()

        pkg = MarketingContentService.generate(feature=FEATURE, descripcion=DESCRIPCION, fecha=FAKE_DATE)
        assert pkg.fallback_used is True

    @patch("taller.services.marketing_content_service._requests.post")
    @patch("taller.services.marketing_content_service.settings")
    def test_fallback_on_http_error(self, mock_settings, mock_post):
        mock_settings.ANTHROPIC_API_KEY = "sk-test-fake-key"
        mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
        err_resp = MagicMock()
        err_resp.ok = False
        err_resp.status_code = 500
        mock_post.return_value = err_resp

        pkg = MarketingContentService.generate(feature=FEATURE, descripcion=DESCRIPCION, fecha=FAKE_DATE)
        assert pkg.fallback_used is True

    @patch("taller.services.marketing_content_service._requests.post")
    @patch("taller.services.marketing_content_service.settings")
    def test_api_key_not_in_response_output(self, mock_settings, mock_post):
        secret = "sk-ant-supersecret-key-12345"
        mock_settings.ANTHROPIC_API_KEY = secret
        mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
        mock_post.return_value = _make_api_response(_VALID_AI_RESPONSE)

        pkg = MarketingContentService.generate(feature=FEATURE, descripcion=DESCRIPCION, fecha=FAKE_DATE)
        output = json.dumps(pkg.to_dict())
        assert secret not in output

    @patch("taller.services.marketing_content_service._requests.post")
    @patch("taller.services.marketing_content_service.settings")
    def test_ai_content_differs_per_network(self, mock_settings, mock_post):
        mock_settings.ANTHROPIC_API_KEY = "sk-test-fake-key"
        mock_settings.ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
        mock_post.return_value = _make_api_response(_VALID_AI_RESPONSE)

        pkg = MarketingContentService.generate(feature=FEATURE, descripcion=DESCRIPCION, fecha=FAKE_DATE)
        assert pkg.facebook["texto"] != pkg.instagram["texto"]
        assert pkg.instagram["texto"] != pkg.tiktok["guion"]
