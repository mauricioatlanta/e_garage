"""
taller/services/marketing_content_service.py — Marketing Content Generator

Genera paquetes de contenido de redes sociales usando Claude vía REST.
Diseñado para ser llamado desde el management command generar_contenido_marketing.

Reglas de privacidad:
  Los prompts NUNCA contienen: IDs, patentes, RUTs, emails de clientes,
  teléfonos, ni datos operacionales privados. Solo la descripción de la
  funcionalidad proporcionada por el operador.

Fallback: determinista, sin red, siempre exitoso cuando falta API key o
          el proveedor devuelve respuesta inválida.
"""
from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from datetime import timezone as _dt_tz

import requests as _requests
from django.conf import settings

logger = logging.getLogger(__name__)

FORMAT_VERSION = "1.0"

# (connect_timeout, read_timeout) — nunca un entero simple para evitar colgar
_TIMEOUT = (3.05, 20)

_HTML_TAG_RE = re.compile(r"<[^>]{0,200}>")


def _clean(text: str) -> str:
    """Remueve etiquetas HTML del output del modelo; preserva emojis y saltos de línea."""
    return _HTML_TAG_RE.sub("", text).strip()


def slugify(text: str) -> str:
    """Slug ASCII seguro para nombre de carpeta, máx 50 chars."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:50] or "sin-nombre"


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketingPackage:
    feature: str
    descripcion: str
    fecha: date
    idioma: str
    publico_objetivo: str
    pais: str
    propuesta_valor: str
    facebook: dict       # {"texto": str}
    instagram: dict      # {"texto": str}
    tiktok: dict         # {gancho, guion, texto_pantalla, escenas, cta}
    reel: dict           # {"escenas": [{tiempo, texto, visual}]}
    historias: list      # [{pantalla, texto, cta}]
    hashtags: list       # [str]
    fallback_used: bool
    modelo: str

    def to_dict(self) -> dict:
        return {
            "feature":          self.feature,
            "descripcion":      self.descripcion,
            "fecha":            self.fecha.isoformat(),
            "idioma":           self.idioma,
            "publico_objetivo": self.publico_objetivo,
            "pais":             self.pais,
            "propuesta_valor":  self.propuesta_valor,
            "redes": {
                "facebook":  self.facebook,
                "instagram": self.instagram,
                "tiktok":    self.tiktok,
                "reel":      self.reel,
                "historias": self.historias,
            },
            "hashtags":       self.hashtags,
            "proveedor":      "anthropic",
            "fallback_used":  self.fallback_used,
            "modelo":         self.modelo,
            "formato_version": FORMAT_VERSION,
        }


# ---------------------------------------------------------------------------
# AI provider
# ---------------------------------------------------------------------------

class MarketingAIError(Exception):
    pass


class MarketingAIProvider:
    _ENDPOINT = "https://api.anthropic.com/v1/messages"

    @staticmethod
    def _get_model() -> str:
        return getattr(settings, "ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    @staticmethod
    def _build_prompt(feature: str, descripcion: str, publico: str, pais: str) -> tuple[str, str]:
        system = (
            "Eres un experto en marketing digital para SaaS B2B en Latinoamérica. "
            "Generas contenido de marketing para eGarage, plataforma de gestión para "
            "talleres mecánicos, casas de repuestos y desarmadurías en Latinoamérica. "
            "Responde ÚNICAMENTE con JSON válido, sin markdown, sin etiquetas HTML, "
            "sin texto adicional. No inventes estadísticas ni cifras. "
            "Adapta el tono a cada red: Facebook profesional y cercano (2-3 párrafos), "
            "Instagram breve y visual (máx 5 líneas con emojis moderados), "
            "TikTok con gancho inmediato en la primera oración."
        )

        # Armamos el template JSON de respuesta esperada como string literal
        json_template = (
            '{\n'
            '  "propuesta_valor": "frase corta que resume el valor de esta funcionalidad",\n'
            '  "facebook": {"texto": "2-3 párrafos, profesional y cercano, CTA a egarage.cl al final"},\n'
            '  "instagram": {"texto": "máx 5 líneas, emojis moderados, tono dinámico"},\n'
            '  "tiktok": {\n'
            '    "gancho": "primera oración que captura atención en 2 segundos",\n'
            '    "guion": "locución completa 20-30 segundos, conversacional",\n'
            '    "texto_pantalla": ["línea corta 1", "línea corta 2", "línea corta 3"],\n'
            '    "escenas": ["escena 1: descripción visual breve", "escena 2: descripción visual breve", "escena 3: descripción visual breve"],\n'
            '    "cta": "llamada a la acción final"\n'
            '  },\n'
            '  "reel": {\n'
            '    "escenas": [\n'
            '      {"tiempo": "0-5s", "texto": "texto en pantalla", "visual": "descripción de lo que se ve"},\n'
            '      {"tiempo": "5-12s", "texto": "texto en pantalla", "visual": "descripción de lo que se ve"},\n'
            '      {"tiempo": "12-20s", "texto": "texto en pantalla", "visual": "descripción de lo que se ve"},\n'
            '      {"tiempo": "20-27s", "texto": "texto en pantalla", "visual": "descripción de lo que se ve"}\n'
            '    ]\n'
            '  },\n'
            '  "historias": [\n'
            '    {"pantalla": 1, "texto": "texto breve pantalla 1", "cta": false},\n'
            '    {"pantalla": 2, "texto": "texto breve pantalla 2", "cta": false},\n'
            '    {"pantalla": 3, "texto": "texto breve pantalla 3", "cta": false},\n'
            '    {"pantalla": 4, "texto": "texto breve pantalla 4", "cta": false},\n'
            '    {"pantalla": 5, "texto": "Pruébalo gratis en egarage.cl", "cta": true}\n'
            '  ],\n'
            '  "hashtags": ["eGarage", "TallerMecanico", "GestionTaller", "SoftwareTaller"]\n'
            '}'
        )

        user = (
            f"Funcionalidad: {feature}\n"
            f"Descripción: {descripcion}\n"
            f"Público objetivo: {publico}\n"
            f"País/región: {pais}\n"
            f"URL del producto: egarage.cl\n\n"
            f"Genera el paquete completo en JSON con exactamente esta estructura:\n"
            f"{json_template}"
        )
        return system, user

    @staticmethod
    def _parse(raw: str) -> dict:
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError as exc:
            raise MarketingAIError(f"JSON inválido: {exc}") from exc

        def _req_str(obj: dict, key: str, maxlen: int = 3000) -> str:
            v = obj.get(key)
            if not isinstance(v, str) or not v.strip():
                raise MarketingAIError(f"'{key}' faltante o vacío")
            if len(v) > maxlen:
                raise MarketingAIError(f"'{key}' supera {maxlen} chars")
            return _clean(v)

        propuesta_valor = _req_str(data, "propuesta_valor", 300)

        fb = data.get("facebook", {})
        if not isinstance(fb, dict):
            raise MarketingAIError("'facebook' debe ser objeto")
        facebook = {"texto": _req_str(fb, "texto", 3000)}

        ig = data.get("instagram", {})
        if not isinstance(ig, dict):
            raise MarketingAIError("'instagram' debe ser objeto")
        instagram = {"texto": _req_str(ig, "texto", 800)}

        tk = data.get("tiktok", {})
        if not isinstance(tk, dict):
            raise MarketingAIError("'tiktok' debe ser objeto")
        tiktok = {
            "gancho":         _req_str(tk, "gancho", 200),
            "guion":          _req_str(tk, "guion", 1500),
            "texto_pantalla": _validated_str_list(tk.get("texto_pantalla"), "tiktok.texto_pantalla", 1, 10),
            "escenas":        _validated_str_list(tk.get("escenas"), "tiktok.escenas", 1, 10),
            "cta":            _req_str(tk, "cta", 200),
        }

        reel_raw = data.get("reel", {})
        if not isinstance(reel_raw, dict):
            raise MarketingAIError("'reel' debe ser objeto")
        escenas_reel = reel_raw.get("escenas", [])
        if not isinstance(escenas_reel, list) or not escenas_reel:
            raise MarketingAIError("'reel.escenas' debe ser lista no vacía")
        reel_escenas = []
        for i, e in enumerate(escenas_reel[:8]):
            if not isinstance(e, dict):
                raise MarketingAIError(f"'reel.escenas[{i}]' debe ser objeto")
            reel_escenas.append({
                "tiempo": _clean(str(e.get("tiempo", ""))),
                "texto":  _clean(str(e.get("texto", ""))),
                "visual": _clean(str(e.get("visual", ""))),
            })
        reel = {"escenas": reel_escenas}

        historias_raw = data.get("historias", [])
        if not isinstance(historias_raw, list) or len(historias_raw) < 3:
            raise MarketingAIError("'historias' debe tener al menos 3 pantallas")
        historias = []
        for i, h in enumerate(historias_raw[:7]):
            if not isinstance(h, dict):
                raise MarketingAIError(f"'historias[{i}]' debe ser objeto")
            historias.append({
                "pantalla": int(h.get("pantalla", i + 1)),
                "texto":    _clean(str(h.get("texto", ""))),
                "cta":      bool(h.get("cta", False)),
            })

        hashtags = _validated_str_list(data.get("hashtags"), "hashtags", 3, 25)

        return {
            "propuesta_valor": propuesta_valor,
            "facebook":        facebook,
            "instagram":       instagram,
            "tiktok":          tiktok,
            "reel":            reel,
            "historias":       historias,
            "hashtags":        hashtags,
        }

    @staticmethod
    def call(feature: str, descripcion: str, publico: str, pais: str) -> tuple[dict, str]:
        """Llama a la API y retorna (datos_validados, modelo). Raises MarketingAIError en fallo."""
        api_key = getattr(settings, "ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise MarketingAIError("ANTHROPIC_API_KEY no configurado")

        model = MarketingAIProvider._get_model()
        system, user = MarketingAIProvider._build_prompt(feature, descripcion, publico, pais)

        payload = {
            "model":      model,
            "max_tokens": 2048,
            "system":     system,
            "messages":   [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
        }

        t0 = time.monotonic()
        try:
            resp = _requests.post(
                MarketingAIProvider._ENDPOINT,
                json=payload,
                headers=headers,
                timeout=_TIMEOUT,
            )
        except _requests.exceptions.Timeout as exc:
            logger.warning("marketing_content: timeout después de %.0fs", time.monotonic() - t0)
            raise MarketingAIError("Timeout en API de Anthropic") from exc
        except _requests.exceptions.RequestException as exc:
            raise MarketingAIError(f"Error de conexión: {exc}") from exc

        if not resp.ok:
            raise MarketingAIError(f"API retornó HTTP {resp.status_code}")

        try:
            raw_text = resp.json()["content"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            raise MarketingAIError(f"Respuesta inesperada del API: {exc}") from exc

        data = MarketingAIProvider._parse(raw_text)
        logger.info(
            "marketing_content: AI success model=%s latency_ms=%d",
            model, int((time.monotonic() - t0) * 1000),
        )
        return data, model


# ---------------------------------------------------------------------------
# Fallback determinista
# ---------------------------------------------------------------------------

class MarketingFallback:

    @staticmethod
    def generate(feature: str, descripcion: str, publico: str, pais: str) -> dict:
        """Genera contenido plantilla sin red. Siempre tiene éxito."""
        desc_short = descripcion[:120] + ("…" if len(descripcion) > 120 else "")

        facebook_texto = (
            f"¡Nuevo en eGarage! 🚗\n\n"
            f"{feature}\n\n"
            f"{descripcion}\n\n"
            f"Diseñado para {publico.lower() if publico else 'talleres mecánicos en Latinoamérica'}. "
            f"Sin complicaciones, desde el primer día.\n\n"
            f"Conoce más en egarage.cl"
        )

        instagram_texto = (
            f"⚡ {feature}\n"
            f"{desc_short}\n"
            f"Tu taller, más inteligente.\n"
            f"👉 egarage.cl"
        )

        tiktok = {
            "gancho":  f"¿Tu taller todavía trabaja sin {feature.lower()}?",
            "guion":   (
                f"Escucha esto. {feature} ya está disponible en eGarage. "
                f"{descripcion} "
                f"Entra a egarage.cl y empieza gratis hoy."
            ),
            "texto_pantalla": [
                feature.upper(),
                "Disponible en eGarage",
                "egarage.cl",
            ],
            "escenas": [
                f"escena 1: pantalla del dashboard mostrando {feature}",
                "escena 2: dueño del taller revisando la información en su celular",
                "escena 3: logo de eGarage con URL egarage.cl",
            ],
            "cta": "Empieza gratis en egarage.cl",
        }

        reel = {
            "escenas": [
                {"tiempo": "0-5s",  "texto": feature.upper(), "visual": f"Pantalla del dashboard mostrando {feature}"},
                {"tiempo": "5-12s", "texto": desc_short[:60], "visual": "Animación de los datos en pantalla"},
                {"tiempo": "12-20s","texto": "Tu taller, más inteligente", "visual": "Dueño satisfecho revisando el celular"},
                {"tiempo": "20-27s","texto": "egarage.cl", "visual": "Logo eGarage con URL en primer plano"},
            ]
        }

        historias = [
            {"pantalla": 1, "texto": f"⚡ Nuevo en eGarage", "cta": False},
            {"pantalla": 2, "texto": feature, "cta": False},
            {"pantalla": 3, "texto": desc_short[:80], "cta": False},
            {"pantalla": 4, "texto": "Disponible ahora para tu taller", "cta": False},
            {"pantalla": 5, "texto": "Pruébalo gratis en egarage.cl", "cta": True},
        ]

        hashtags = [
            "eGarage", "TallerMecanico", "GestionTaller", "SoftwareTaller",
            "Repuestos", "AutoLatam", "TallerInteligente",
        ]

        return {
            "propuesta_valor": f"{feature} — gestión más inteligente para tu taller",
            "facebook":        {"texto": facebook_texto},
            "instagram":       {"texto": instagram_texto},
            "tiktok":          tiktok,
            "reel":            reel,
            "historias":       historias,
            "hashtags":        hashtags,
        }


# ---------------------------------------------------------------------------
# Servicio principal
# ---------------------------------------------------------------------------

class MarketingContentService:

    @staticmethod
    def generate(
        feature: str,
        descripcion: str,
        publico: str = "Dueños de talleres mecánicos y casas de repuestos en Latinoamérica",
        idioma: str = "es",
        pais: str = "CL",
        fecha: date | None = None,
    ) -> MarketingPackage:
        """
        Genera un MarketingPackage.
        Si falta ANTHROPIC_API_KEY o el proveedor falla, usa el fallback determinista.
        No lanza excepciones al llamador (salvo ValueError por args inválidos).
        """
        feature = feature.strip()
        descripcion = descripcion.strip()
        if not feature:
            raise ValueError("feature no puede estar vacío")
        if not descripcion:
            raise ValueError("descripcion no puede estar vacía")

        fecha = fecha or date.today()
        api_key = getattr(settings, "ANTHROPIC_API_KEY", "").strip()

        if not api_key:
            logger.info("marketing_content: sin API key — usando fallback")
            data = MarketingFallback.generate(feature, descripcion, publico, pais)
            return _assemble(feature, descripcion, fecha, idioma, publico, pais, data, True, "")

        try:
            data, model = MarketingAIProvider.call(feature, descripcion, publico, pais)
            return _assemble(feature, descripcion, fecha, idioma, publico, pais, data, False, model)
        except MarketingAIError as exc:
            logger.warning("marketing_content: AI falló, usando fallback. %s", exc)
            data = MarketingFallback.generate(feature, descripcion, publico, pais)
            return _assemble(feature, descripcion, fecha, idioma, publico, pais, data, True, "")


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _validated_str_list(value: object, field: str, min_len: int, max_len: int) -> list[str]:
    if not isinstance(value, list) or len(value) < min_len:
        raise MarketingAIError(f"'{field}' debe ser lista con al menos {min_len} elemento(s)")
    if len(value) > max_len:
        value = value[:max_len]
    result = []
    for i, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise MarketingAIError(f"'{field}[{i}]' debe ser string no vacío")
        result.append(_clean(item))
    return result


def _assemble(
    feature: str,
    descripcion: str,
    fecha: date,
    idioma: str,
    publico: str,
    pais: str,
    data: dict,
    fallback_used: bool,
    modelo: str,
) -> MarketingPackage:
    return MarketingPackage(
        feature=feature,
        descripcion=descripcion,
        fecha=fecha,
        idioma=idioma,
        publico_objetivo=publico,
        pais=pais,
        propuesta_valor=data["propuesta_valor"],
        facebook=data["facebook"],
        instagram=data["instagram"],
        tiktok=data["tiktok"],
        reel=data["reel"],
        historias=data["historias"],
        hashtags=data["hashtags"],
        fallback_used=fallback_used,
        modelo=modelo,
    )
