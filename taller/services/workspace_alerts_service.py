"""
taller/services/workspace_alerts_service.py — Workspace Alerts (Fase 4)

Resolves actionable alerts for a workspace + empresa pair.

Contract:
  - Receives: WorkspaceDef, Empresa, prefix (URL prefix "/cl/es" etc.), optional date.
  - Returns: list of alert dicts — no lazy querysets, no deferred evaluation.
  - Exactly 2 SQL queries for DESARMADURIA (one per table group).
  - All other workspaces: 0 queries, returns [] immediately.
  - Only alerts with count > 0 are included in the result.
  - Never renders HTML.

Query groups (DESARMADURIA only):
  GROUP_VEHICULOS  VehiculoDesarme → alrt_desarm_delayed
  GROUP_PIEZAS     PiezaDesarme    → alrt_pieza_no_foto
                                      alrt_pieza_no_precio
                                      alrt_pieza_no_ubicacion

Alert dict structure:
  {
    "key":      str,     # ALRT_* constant
    "severity": str,     # "warning" | "info"
    "message":  str,     # human-readable, already pluralised
    "count":    int,     # raw number (> 0)
    "url":      str,     # pre-filtered list URL including prefix
    "icon":     str,     # FontAwesome class
  }
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count, Q

from taller.constants.product_profiles import PRODUCT_DESARMADURIA
from taller.constants.workspaces import WorkspaceDef

# ---------------------------------------------------------------------------
# Public constants — imported by view (for URL injection) and tests.
# ---------------------------------------------------------------------------
ALRT_DESARM_DELAYED    = "alrt_desarm_delayed"
ALRT_PIEZA_NO_FOTO     = "alrt_pieza_no_foto"
ALRT_PIEZA_NO_PRECIO   = "alrt_pieza_no_precio"
ALRT_PIEZA_NO_UBICACION = "alrt_pieza_no_ubicacion"

DELAYED_DAYS = 30  # threshold for "stuck" vehicles


class WorkspaceAlertsService:

    @staticmethod
    def resolve(
        workspace_def: WorkspaceDef,
        empresa,
        prefix: str = "/cl/es",
        today: date | None = None,
    ) -> list[dict]:
        """
        Returns active alerts for the workspace.

        DESARMADURIA: exactly 2 SQL queries.
        All other workspaces: [] with 0 queries.
        """
        if workspace_def.product_key != PRODUCT_DESARMADURIA:
            return []

        today = today or date.today()
        cutoff = today - timedelta(days=DELAYED_DAYS)

        alerts: list[dict] = []

        # ── Query 1: VehiculoDesarme ──────────────────────────────────────
        delayed = WorkspaceAlertsService._query_delayed(empresa, cutoff)
        if delayed > 0:
            noun = "vehículo" if delayed == 1 else "vehículos"
            alerts.append({
                "key":      ALRT_DESARM_DELAYED,
                "severity": "warning",
                "message":  f"{delayed} {noun} con más de {DELAYED_DAYS} días sin avanzar",
                "count":    delayed,
                "url":      (
                    f"{prefix}/desarme/vehiculos/"
                    f"?estado=INGRESADO,DESARMANDO"
                    f"&ingresado_antes={cutoff.isoformat()}"
                ),
                "icon": "fas fa-clock",
            })

        # ── Query 2: PiezaDesarme (3 conditional Count in 1 aggregate) ───
        agg = WorkspaceAlertsService._query_piezas(empresa)

        _PIEZA_DEFS: tuple[tuple, ...] = (
            (
                agg["sin_foto"],
                ALRT_PIEZA_NO_FOTO,
                "info",
                "fas fa-camera",
                f"{prefix}/desarme/piezas/?estado=DISPONIBLE&sin_foto=1",
                "pieza sin fotografía",
                "piezas sin fotografía",
            ),
            (
                agg["sin_precio"],
                ALRT_PIEZA_NO_PRECIO,
                "info",
                "fas fa-tag",
                f"{prefix}/desarme/piezas/?estado=DISPONIBLE&sin_precio=1",
                "pieza sin precio",
                "piezas sin precio",
            ),
            (
                agg["sin_ubicacion"],
                ALRT_PIEZA_NO_UBICACION,
                "info",
                "fas fa-map-marker-alt",
                f"{prefix}/desarme/piezas/?estado=DISPONIBLE&sin_ubicacion=1",
                "pieza sin ubicación física",
                "piezas sin ubicación física",
            ),
        )

        for count, key, severity, icon, url, singular, plural in _PIEZA_DEFS:
            if count > 0:
                noun = singular if count == 1 else plural
                alerts.append({
                    "key":      key,
                    "severity": severity,
                    "message":  f"{count} {noun}",
                    "count":    count,
                    "url":      url,
                    "icon":     icon,
                })

        return alerts

    # ------------------------------------------------------------------
    # Query groups — 1 method per table, each executes 1 SQL query.
    # ------------------------------------------------------------------

    @staticmethod
    def _query_delayed(empresa, cutoff: date) -> int:
        from taller.models.vehiculo_desarme import VehiculoDesarme

        return VehiculoDesarme.objects.filter(
            empresa=empresa,
            es_placeholder=False,
            estado_desarme__in=["INGRESADO", "DESARMANDO"],
            fecha_ingreso_desarme__isnull=False,
            fecha_ingreso_desarme__lt=cutoff,
        ).count()

    @staticmethod
    def _query_piezas(empresa) -> dict:
        from taller.models.pieza_desarme import PiezaDesarme

        return PiezaDesarme.objects.filter(
            empresa=empresa,
            activo=True,
            estado_pieza__in=["DISPONIBLE", "RESERVADA"],
        ).aggregate(
            sin_foto=Count(
                "id",
                filter=Q(imagen__isnull=True) | Q(imagen=""),
            ),
            sin_precio=Count(
                "id",
                filter=Q(precio_venta_sugerido__isnull=True) & Q(precio_sugerido__isnull=True),
            ),
            sin_ubicacion=Count(
                "id",
                filter=Q(ubicacion_fisica__isnull=True),
            ),
        )
