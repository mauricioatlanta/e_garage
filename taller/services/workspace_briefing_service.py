"""
taller/services/workspace_briefing_service.py — Workspace AI Briefing v1

Genera un resumen operativo diario usando Claude Haiku. Solo para DESARMADURIA.
Para otros rubros retorna fallback inmediato sin queries ni API calls.

Reglas de privacidad:
  El prompt NUNCA contiene: IDs, URLs, patentes, RUTs, emails, teléfonos
  ni nombres de clientes. Solo métricas numéricas y etiquetas del workspace.

Cache:  briefing:v1:{empresa_id}:{product_key}:{date}:{lang}
        TTL: settings.BRIEFING_CACHE_TTL (1800 s)
Budget: briefing:budget:{empresa_id}:{localdate}
        límite: settings.BRIEFING_DAILY_LIMIT (10) — por empresa, por día calendario

Query cost:
  HIT  → 0 queries, 0 HTTP
  MISS → 4 queries (WorkspaceDashboardService + WorkspaceAlertsService) + 1 HTTP
         (o 0 HTTP si fallback)
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from datetime import timezone as _dt_tz

import requests as _requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone as _dj_tz

from taller.constants.product_profiles import PRODUCT_DESARMADURIA
from taller.constants.workspaces import WorkspaceDef

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Validation limits applied to the AI response
# ---------------------------------------------------------------------------

_MAX_GREETING_LEN  = 80
_MAX_SUMMARY_ITEMS = 5
_MAX_ITEM_LEN      = 300
_MAX_REC_LEN       = 300

# Max alerts passed into the prompt context (controls prompt size, not DB)
_MAX_ALERTS_IN_CONTEXT = 5

# Severities our alert service produces; used to filter stale/corrupt data
_VALID_SEVERITIES = frozenset({"info", "warning"})

# Patterns to strip from AI output before storing or returning
_HTML_TAG_RE    = re.compile(r"<[^>]{0,200}>")
_MARKDOWN_RE    = re.compile(r"[*_`#\[\]()!]")

# ---------------------------------------------------------------------------
# Prompt version — bump this when the system/user prompt content changes.
# Logged on every call so you can correlate fallback rate with prompt versions
# without checking git history.
# ---------------------------------------------------------------------------

PROMPT_VERSION = "v1"

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_RUBRO_LABELS: dict[str, str] = {
    PRODUCT_DESARMADURIA: "Desarmaduría / Salvage",
    "TALLER":             "Taller mecánico",
    "CASA_REPUESTOS":     "Casa de repuestos",
    "CARWASH":            "Carwash / Lavado",
}

_MONTHS_ES = (
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

_SYSTEM_ES = (
    "Eres el asistente operativo de {empresa_nombre}, {rubro_label}. "
    "Genera un resumen operativo del día en español. "
    "Responde ÚNICAMENTE con JSON válido, sin markdown, sin etiquetas HTML, "
    "sin texto adicional. No inventes datos. Usa solo los números que te proporciono. "
    'Formato exacto: {{"greeting":"string ≤12 palabras",'
    '"summary":["frase 1","frase 2"],"recommendation":"string ≤25 palabras"}}'
)

_SYSTEM_EN = (
    "You are the operational assistant for {empresa_nombre}, a {rubro_label}. "
    "Generate a daily operational summary in English. "
    "Respond ONLY with valid JSON, no markdown, no HTML tags, no extra text. "
    "Do not invent data. Use only the numbers I provide. "
    'Exact format: {{"greeting":"string ≤12 words",'
    '"summary":["line 1","line 2"],"recommendation":"string ≤25 words"}}'
)


# ---------------------------------------------------------------------------
# Markup sanitiser — applied to every AI string before use
# ---------------------------------------------------------------------------

def _strip_markup(text: str) -> str:
    """Removes HTML tags and markdown special characters from model output."""
    text = _HTML_TAG_RE.sub("", text)
    return _MARKDOWN_RE.sub("", text).strip()


# ---------------------------------------------------------------------------
# Structured event logger — metadata only, never logs prompts or responses
# ---------------------------------------------------------------------------

def _log_event(
    *,
    empresa_id: int,
    product_key: str,
    event: str,
    model: str = "",
    prompt_version: str = PROMPT_VERSION,
    latency_ms: int | None = None,
    cache_hit: bool = False,
    fallback_used: bool = False,
    status_code: int | None = None,
    validation_error_type: str | None = None,
) -> None:
    logger.info(
        "workspace_briefing %s",
        event,
        extra={
            "empresa_id":            empresa_id,
            "product_key":           product_key,
            "provider":              "anthropic",
            "model":                 model,
            "prompt_version":        prompt_version,
            "latency_ms":            latency_ms,
            "cache_hit":             cache_hit,
            "fallback_used":         fallback_used,
            "status_code":           status_code,
            "validation_error_type": validation_error_type,
        },
    )


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BriefingContext:
    """
    PII-free snapshot of workspace data for the AI prompt.
    No IDs, no URLs, no patentes, no RUTs, no emails, no phone numbers.
    empresa_id is used only for cache/budget keys, never sent to the API.
    """
    empresa_id: int
    empresa_nombre: str
    rubro_label: str
    product_key: str
    kpi_snapshot: tuple[dict, ...]    # [{title, value, format}] — non-zero has_value widgets only
    alert_snapshot: tuple[dict, ...]  # [{message, count, severity}] — no URLs, no icons
    date: date
    lang: str                         # "es" | "en"


@dataclass(frozen=True)
class BriefingResult:
    greeting: str
    summary: tuple[str, ...]
    recommendation: str
    source: str           # "ai" | "fallback"
    cached: bool
    generated_at: str     # ISO 8601 UTC
    model: str            # model ID used, or "" for fallback
    prompt_version: str   # PROMPT_VERSION at generation time; survives in cache


# ---------------------------------------------------------------------------
# BriefingContextBuilder
# ---------------------------------------------------------------------------

class BriefingContextBuilder:

    @staticmethod
    def build(
        empresa,
        ws_def: WorkspaceDef,
        prefix: str,
        lang: str,
        today: date | None = None,
    ) -> BriefingContext:
        """
        Runs dashboard + alert queries and returns a PII-free BriefingContext.
        Never calls the AI. prefix is used to build alert URLs internally but is
        NOT stored in the context (URLs are stripped before returning).

        today defaults to Django's timezone-aware local date (TIME_ZONE setting).
        Pass today explicitly in tests to ensure deterministic date logic.
        """
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService

        today = today or (
            _dj_tz.localdate() if getattr(settings, "USE_TZ", False) else date.today()
        )
        dashboard = WorkspaceDashboardService.resolve(ws_def, empresa, today)
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa, prefix, today)

        kpi_snapshot = tuple(
            {"title": w["title"], "value": w["value"], "format": w["format"]}
            for w in dashboard["widgets"]
            if w.get("has_value") and w.get("value") not in (0, None)
        )
        # Defensive: filter out alerts with unexpected severity, cap at context limit
        alert_snapshot = tuple(
            {"message": a["message"], "count": a["count"], "severity": a["severity"]}
            for a in alerts
            if a.get("severity") in _VALID_SEVERITIES
        )[:_MAX_ALERTS_IN_CONTEXT]

        config = getattr(empresa, "config", None)
        empresa_nombre = (
            (config and getattr(config, "nombre_publico", "")) or
            getattr(empresa, "nombre_taller", "") or
            "la empresa"
        )

        return BriefingContext(
            empresa_id=empresa.pk,
            empresa_nombre=empresa_nombre,
            rubro_label=_RUBRO_LABELS.get(ws_def.product_key, ws_def.product_key),
            product_key=ws_def.product_key,
            kpi_snapshot=kpi_snapshot,
            alert_snapshot=alert_snapshot,
            date=today,
            lang=(lang or "es")[:2],
        )


# ---------------------------------------------------------------------------
# BriefingFallback
# ---------------------------------------------------------------------------

class BriefingFallback:

    @staticmethod
    def generate(ctx: BriefingContext) -> BriefingResult:
        """
        Deterministic text generation from BriefingContext.
        Zero HTTP calls. Zero extra queries. Always succeeds.
        Used when: API key missing, API call fails, budget exhausted, non-DESARMADURIA.
        """
        is_en = ctx.lang == "en"

        if is_en:
            greeting = f"Operational summary for {ctx.date.strftime('%B %-d')}"
        else:
            greeting = f"Resumen operativo del {ctx.date.day} de {_MONTHS_ES[ctx.date.month]}"

        lines: list[str] = []

        for a in ctx.alert_snapshot:
            msg = a["message"]
            lines.append(msg[0].upper() + msg[1:] + ("." if not msg.endswith(".") else ""))

        for kpi in ctx.kpi_snapshot:
            v = kpi["value"]
            if kpi["format"] == "currency":
                try:
                    from decimal import Decimal
                    v = f"${Decimal(str(v)):,.0f}"
                except Exception:
                    v = str(v)
            lines.append(f"{kpi['title']}: {v}.")

        if not lines:
            lines = (
                ["No active alerts. Operations running smoothly."]
                if is_en else
                ["Sin alertas activas. La operación funciona con normalidad."]
            )

        lines = lines[:_MAX_SUMMARY_ITEMS]

        warning_alerts = [a for a in ctx.alert_snapshot if a["severity"] == "warning"]
        info_alerts    = [a for a in ctx.alert_snapshot if a["severity"] == "info"]

        if warning_alerts:
            count = warning_alerts[0]["count"]
            recommendation = (
                f"Address the {count} vehicle(s) stuck in progress immediately."
                if is_en else
                f"Atiende los {count} vehículos atascados cuanto antes."
            )
        elif info_alerts:
            recommendation = (
                "Complete photos and prices on parts to activate them for sales."
                if is_en else
                "Completa fotos y precios de las piezas para activarlas en ventas."
            )
        else:
            recommendation = (
                "Keep up the pace — no pending operational issues."
                if is_en else
                "Mantén el ritmo — no hay alertas operativas pendientes."
            )

        return BriefingResult(
            greeting=greeting,
            summary=tuple(lines),
            recommendation=recommendation,
            source="fallback",
            cached=False,
            generated_at=datetime.now(_dt_tz.utc).isoformat(),
            model="",
            prompt_version=PROMPT_VERSION,
        )


# ---------------------------------------------------------------------------
# BriefingAIProvider
# ---------------------------------------------------------------------------

class BriefingAIError(Exception):
    pass


class BriefingAIProvider:
    _ENDPOINT = "https://api.anthropic.com/v1/messages"
    # (connect_timeout, read_timeout) — never a bare integer to avoid hanging forever
    _TIMEOUT = (3.05, 12)

    @staticmethod
    def _get_model() -> str:
        return getattr(settings, "ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    @staticmethod
    def _build_prompt(ctx: BriefingContext) -> tuple[str, str]:
        """
        Returns (system_prompt, user_prompt).
        Guaranteed to contain NO PII: no IDs, URLs, patentes, emails or phone numbers.
        """
        system_tpl = _SYSTEM_EN if ctx.lang == "en" else _SYSTEM_ES
        system = system_tpl.format(
            empresa_nombre=ctx.empresa_nombre,
            rubro_label=ctx.rubro_label,
        )

        parts = [f"Fecha: {ctx.date.isoformat()}", ""]

        if ctx.kpi_snapshot:
            parts.append("KPIs del día:" if ctx.lang != "en" else "Today's KPIs:")
            for kpi in ctx.kpi_snapshot:
                parts.append(f"  - {kpi['title']}: {kpi['value']}")
            parts.append("")

        if ctx.alert_snapshot:
            parts.append("Alertas activas:" if ctx.lang != "en" else "Active alerts:")
            for a in ctx.alert_snapshot:
                parts.append(f"  - {a['message']}")
        else:
            parts.append(
                "Sin alertas activas." if ctx.lang != "en" else "No active alerts."
            )

        return system, "\n".join(parts)

    @staticmethod
    def _parse_response(raw: str) -> dict:
        """
        Validates the AI JSON response strictly.
        Raises BriefingAIError if the schema, lengths, or content types are invalid.
        Strips markup from all string fields before returning.
        """
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError as exc:
            raise BriefingAIError(f"AI returned invalid JSON: {exc}") from exc

        # greeting
        greeting = data.get("greeting")
        if not isinstance(greeting, str) or not greeting.strip():
            raise BriefingAIError("'greeting' missing or empty")
        if len(greeting) > _MAX_GREETING_LEN:
            raise BriefingAIError(f"'greeting' exceeds {_MAX_GREETING_LEN} chars")

        # summary
        summary = data.get("summary")
        if not isinstance(summary, list) or not summary:
            raise BriefingAIError("'summary' must be a non-empty list")
        if not all(isinstance(s, str) and s.strip() for s in summary):
            raise BriefingAIError("All 'summary' items must be non-empty strings")
        if any(len(s) > _MAX_ITEM_LEN for s in summary):
            raise BriefingAIError(f"A 'summary' item exceeds {_MAX_ITEM_LEN} chars")
        summary = [s for s in summary[:_MAX_SUMMARY_ITEMS] if s.strip()]

        # recommendation
        rec = data.get("recommendation")
        if not isinstance(rec, str) or not rec.strip():
            raise BriefingAIError("'recommendation' missing or empty")
        if len(rec) > _MAX_REC_LEN:
            raise BriefingAIError(f"'recommendation' exceeds {_MAX_REC_LEN} chars")

        return {
            "greeting":       _strip_markup(greeting),
            "summary":        [_strip_markup(s) for s in summary],
            "recommendation": _strip_markup(rec),
        }

    @staticmethod
    def call(ctx: BriefingContext) -> BriefingResult:
        """
        POSTs to Anthropic Messages API using requests.
        Raises BriefingAIError on missing key, timeout, HTTP error, or schema violation.
        Logs only metadata (empresa_id, model, latency_ms, status_code) — never prompt content.
        """
        api_key = getattr(settings, "ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise BriefingAIError("ANTHROPIC_API_KEY not configured")

        model = BriefingAIProvider._get_model()
        system_prompt, user_prompt = BriefingAIProvider._build_prompt(ctx)

        payload = {
            "model":      model,
            "max_tokens": 512,
            "system":     system_prompt,
            "messages":   [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
        }

        t0 = time.monotonic()
        status_code: int | None = None

        try:
            resp = _requests.post(
                BriefingAIProvider._ENDPOINT,
                json=payload,
                headers=headers,
                timeout=BriefingAIProvider._TIMEOUT,
            )
            status_code = resp.status_code
        except _requests.exceptions.Timeout as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            _log_event(
                empresa_id=ctx.empresa_id, product_key=ctx.product_key,
                event="timeout", model=model, latency_ms=latency_ms,
                fallback_used=True, validation_error_type="timeout",
            )
            raise BriefingAIError("Anthropic API timeout") from exc
        except _requests.exceptions.RequestException as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            _log_event(
                empresa_id=ctx.empresa_id, product_key=ctx.product_key,
                event="connection_error", model=model, latency_ms=latency_ms,
                fallback_used=True, validation_error_type="connection_error",
            )
            raise BriefingAIError(f"Anthropic API connection error: {exc}") from exc

        latency_ms = int((time.monotonic() - t0) * 1000)

        if not resp.ok:
            _log_event(
                empresa_id=ctx.empresa_id, product_key=ctx.product_key,
                event="http_error", model=model, latency_ms=latency_ms,
                fallback_used=True, status_code=status_code,
            )
            raise BriefingAIError(f"Anthropic API returned HTTP {status_code}")

        try:
            body = resp.json()
            raw_text = body["content"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            _log_event(
                empresa_id=ctx.empresa_id, product_key=ctx.product_key,
                event="shape_error", model=model, latency_ms=latency_ms,
                fallback_used=True, status_code=status_code,
                validation_error_type="unexpected_shape",
            )
            raise BriefingAIError(f"Unexpected response shape: {exc}") from exc

        try:
            data = BriefingAIProvider._parse_response(raw_text)
        except BriefingAIError as exc:
            _log_event(
                empresa_id=ctx.empresa_id, product_key=ctx.product_key,
                event="validation_error", model=model, latency_ms=latency_ms,
                fallback_used=True, status_code=status_code,
                validation_error_type=type(exc).__name__,
            )
            raise

        _log_event(
            empresa_id=ctx.empresa_id, product_key=ctx.product_key,
            event="success", model=model, prompt_version=PROMPT_VERSION,
            latency_ms=latency_ms, fallback_used=False, status_code=status_code,
        )

        return BriefingResult(
            greeting=data["greeting"],
            summary=tuple(s for s in data["summary"] if s),
            recommendation=data["recommendation"],
            source="ai",
            cached=False,
            generated_at=datetime.now(_dt_tz.utc).isoformat(),
            model=model,
            prompt_version=PROMPT_VERSION,
        )


# ---------------------------------------------------------------------------
# Cache and budget helpers
# ---------------------------------------------------------------------------

def _cache_key(empresa_id: int, product_key: str, date_: date, lang: str) -> str:
    """
    Isolated per empresa + business type + calendar date + language.
    Two empresas with the same rubro never share a briefing.
    """
    return f"briefing:v1:{empresa_id}:{product_key}:{date_.isoformat()}:{lang}"


def _budget_key(empresa_id: int, date_: date) -> str:
    """
    Isolated per empresa + local calendar date.
    Uses the date passed from BriefingContext (set with _dj_tz.localdate()).
    """
    return f"briefing:budget:{empresa_id}:{date_.isoformat()}"


def _budget_remaining(empresa_id: int, date_: date) -> int:
    limit = getattr(settings, "BRIEFING_DAILY_LIMIT", 10)
    used = cache.get(_budget_key(empresa_id, date_), 0)
    return max(0, limit - used)


def _increment_budget(empresa_id: int, date_: date) -> None:
    key = _budget_key(empresa_id, date_)
    try:
        cache.incr(key)
    except ValueError:
        # Key doesn't exist yet — race condition window is negligible at the scale
        # of 10 calls/day/empresa; set to 1 rather than over-block.
        cache.set(key, 1, 86400)


# ---------------------------------------------------------------------------
# WorkspaceBriefingService
# ---------------------------------------------------------------------------

class WorkspaceBriefingService:

    @staticmethod
    def resolve(ctx: BriefingContext) -> BriefingResult:
        """
        Main entry point.
        Flow: cache HIT → return  |  cache MISS → AI (if key+budget) → fallback
        Both AI and fallback results are cached for BRIEFING_CACHE_TTL seconds.
        """
        if ctx.product_key != PRODUCT_DESARMADURIA:
            return BriefingFallback.generate(ctx)

        ttl = getattr(settings, "BRIEFING_CACHE_TTL", 1800)
        key = _cache_key(ctx.empresa_id, ctx.product_key, ctx.date, ctx.lang)

        cached = cache.get(key)
        if cached is not None:
            _log_event(
                empresa_id=ctx.empresa_id, product_key=ctx.product_key,
                event="cache_hit", cache_hit=True,
                model=cached.get("model", ""),
                prompt_version=cached.get("prompt_version", PROMPT_VERSION),
            )
            return BriefingResult(
                greeting=cached["greeting"],
                summary=tuple(cached["summary"]),
                recommendation=cached["recommendation"],
                source=cached["source"],
                cached=True,
                generated_at=cached["generated_at"],
                model=cached.get("model", ""),
                prompt_version=cached.get("prompt_version", PROMPT_VERSION),
            )

        api_key = getattr(settings, "ANTHROPIC_API_KEY", "").strip()
        result: BriefingResult

        if api_key and _budget_remaining(ctx.empresa_id, ctx.date) > 0:
            try:
                result = BriefingAIProvider.call(ctx)
                _increment_budget(ctx.empresa_id, ctx.date)
            except BriefingAIError as exc:
                logger.warning(
                    "workspace_briefing AI failed — falling back",
                    extra={
                        "empresa_id":  ctx.empresa_id,
                        "product_key": ctx.product_key,
                        "error_type":  type(exc).__name__,
                    },
                )
                result = BriefingFallback.generate(ctx)
        else:
            _log_event(
                empresa_id=ctx.empresa_id, product_key=ctx.product_key,
                event="fallback_no_key_or_budget", fallback_used=True,
            )
            result = BriefingFallback.generate(ctx)

        cache.set(key, {
            "greeting":        result.greeting,
            "summary":         list(result.summary),
            "recommendation":  result.recommendation,
            "source":          result.source,
            "generated_at":    result.generated_at,
            "model":           result.model,
            "prompt_version":  result.prompt_version,
        }, ttl)

        return result
