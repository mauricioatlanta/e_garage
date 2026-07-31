"""
taller/services/workspace_dashboard_service.py — Workspace UI 2.0

Resolves dashboard data for a given WorkspaceDef and Empresa.

Contract:
  - Receives: WorkspaceDef, Empresa instance, optional date (defaults to today)
  - Returns: concrete dict — no lazy querysets, no deferred evaluation.
  - Groups all ORM queries by table; at most 4 queries regardless of widget count.
  - Never renders HTML.

Widget query groups (each group = 1 SQL query max):
  GROUP_DOCS      Documento table  → kpi_ot_open, kpi_docs_today,
                                      kpi_sales_today, kpi_services_today
  GROUP_CLIENTS   Cliente table    → kpi_clients_month
  GROUP_INVENTORY Repuesto table   → kpi_stock_critical, kpi_inventory_value
  GROUP_DESARM    VehiculoDesarme  → kpi_desarm_available

Dashboard data structure:
  {
    "widgets": [
        {"key": str, "title": str, "icon": str, "value": int|Decimal, "format": str},
        ...
    ],
    "date": date,
  }
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from taller.constants.workspaces import (
    WGT_KPI_CLIENTS_MONTH,
    WGT_KPI_DESARM_AVAIL,
    WGT_KPI_DOCS_TODAY,
    WGT_KPI_INVENTORY_VALUE,
    WGT_KPI_MARGIN_MONTH,
    WGT_KPI_OT_OPEN,
    WGT_KPI_QUOTES_PENDING,
    WGT_KPI_SALES_TODAY,
    WGT_KPI_SERVICES_TODAY,
    WGT_KPI_STOCK_CRITICAL,
    WorkspaceDef,
)

MIN_MARGIN_COST_COVERAGE = Decimal("30.00")  # % of STOCK_BODEGA lines that must have costo_linea

_ZERO_DEC = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))

# Widget metadata: title (translated), icon, display format.
# "number"   → plain integer
# "currency" → formatted as money (template adds currency symbol)
WIDGET_DEFINITIONS: dict[str, dict] = {
    WGT_KPI_OT_OPEN:         {"title": _("OT Abiertas"),               "icon": "fas fa-clipboard-list",      "format": "number"},
    WGT_KPI_DOCS_TODAY:      {"title": _("Documentos hoy"),             "icon": "fas fa-file-alt",            "format": "number"},
    WGT_KPI_SALES_TODAY:     {"title": _("Ventas del día"),             "icon": "fas fa-dollar-sign",         "format": "currency"},
    WGT_KPI_CLIENTS_MONTH:   {"title": _("Clientes este mes"),          "icon": "fas fa-user-plus",           "format": "number"},
    WGT_KPI_STOCK_CRITICAL:  {"title": _("Stock crítico"),              "icon": "fas fa-exclamation-triangle","format": "number"},
    WGT_KPI_DESARM_AVAIL:    {"title": _("Vehículos disponibles"),      "icon": "fas fa-car-crash",           "format": "number"},
    WGT_KPI_INVENTORY_VALUE: {"title": _("Valor inventario"),           "icon": "fas fa-boxes",               "format": "currency"},
    WGT_KPI_SERVICES_TODAY:  {"title": _("Servicios hoy"),              "icon": "fas fa-tint",                "format": "number"},
    WGT_KPI_QUOTES_PENDING:  {"title": _("Cotizaciones pendientes"),    "icon": "fas fa-hourglass-half",      "format": "number"},
    WGT_KPI_MARGIN_MONTH:    {"title": _("Margen del mes"),             "icon": "fas fa-percentage",          "format": "percent"},
}

# Which widget keys belong to each query group
_GROUP_DOCS      = frozenset({WGT_KPI_OT_OPEN, WGT_KPI_DOCS_TODAY, WGT_KPI_SALES_TODAY, WGT_KPI_SERVICES_TODAY, WGT_KPI_QUOTES_PENDING})
_GROUP_CLIENTS   = frozenset({WGT_KPI_CLIENTS_MONTH})
_GROUP_INVENTORY = frozenset({WGT_KPI_STOCK_CRITICAL, WGT_KPI_INVENTORY_VALUE})
_GROUP_DESARM    = frozenset({WGT_KPI_DESARM_AVAIL})
_GROUP_LINEAS    = frozenset({WGT_KPI_MARGIN_MONTH})


class WorkspaceDashboardService:

    @staticmethod
    def resolve(workspace_def: WorkspaceDef, empresa, today: date | None = None) -> dict:
        """
        Executes batch ORM queries and returns a concrete dashboard_data dict.

        At most 4 SQL queries (one per table group). Only the groups whose
        widget keys appear in workspace_def.widget_keys are executed.
        """
        needed = frozenset(workspace_def.widget_keys)
        today = today or date.today()
        month_start = date(today.year, today.month, 1)
        next_month_start = (
            date(today.year + 1, 1, 1) if today.month == 12
            else date(today.year, today.month + 1, 1)
        )

        raw: dict = {}

        # ── GROUP 1: Documento table ──────────────────────────────────────
        if needed & _GROUP_DOCS:
            raw.update(WorkspaceDashboardService._query_docs(empresa, today))

        # ── GROUP 2: Cliente table ────────────────────────────────────────
        if needed & _GROUP_CLIENTS:
            raw.update(WorkspaceDashboardService._query_clients(empresa, month_start))

        # ── GROUP 3: Repuesto table ───────────────────────────────────────
        if needed & _GROUP_INVENTORY:
            raw.update(WorkspaceDashboardService._query_inventory(empresa))

        # ── GROUP 4: VehiculoDesarme table ───────────────────────────────
        if needed & _GROUP_DESARM:
            raw.update(WorkspaceDashboardService._query_desarm(empresa))

        # ── GROUP 5: LineaRepuesto table (margin) ─────────────────────────
        if needed & _GROUP_LINEAS:
            raw.update(WorkspaceDashboardService._query_lineas(empresa, month_start, next_month_start))

        # Build resolved widget list in workspace-defined order
        widgets = WorkspaceDashboardService._build_widgets(workspace_def.widget_keys, raw)

        return {
            "widgets": widgets,
            "date":    today,
        }

    # ------------------------------------------------------------------
    # Query groups — one method per table, each executes 1 SQL query.
    # ------------------------------------------------------------------

    @staticmethod
    def _query_docs(empresa, today: date) -> dict:
        from taller.models.documento import Documento

        agg = Documento.objects.filter(empresa=empresa).aggregate(
            docs_today=Count("id", filter=Q(fecha_emision=today)),
            sales_today=Coalesce(
                Sum("total", filter=Q(fecha_emision=today)),
                _ZERO_DEC,
            ),
            ot_open=Count("id", filter=Q(tipo="OT", estado="EMITIDO")),
            # Pending quotes: PRES not yet converted (tipo would change on conversion)
            # and not cancelled. Includes BORRADOR (unsent drafts) + EMITIDO (awaiting response).
            quotes_pending=Count("id", filter=Q(tipo="PRES", estado__in=["BORRADOR", "EMITIDO"])),
        )
        return {
            WGT_KPI_DOCS_TODAY:     agg["docs_today"],
            WGT_KPI_SALES_TODAY:    agg["sales_today"],
            WGT_KPI_OT_OPEN:        agg["ot_open"],
            WGT_KPI_QUOTES_PENDING: agg["quotes_pending"],
            # Services today = all docs today (carwash context reuses the count)
            WGT_KPI_SERVICES_TODAY: agg["docs_today"],
        }

    @staticmethod
    def _query_clients(empresa, month_start: date) -> dict:
        from taller.models.clientes import Cliente

        count = Cliente.objects.filter(
            empresa=empresa,
            created_at__date__gte=month_start,
        ).count()
        return {WGT_KPI_CLIENTS_MONTH: count}

    @staticmethod
    def _query_inventory(empresa) -> dict:
        from taller.models.repuesto import Repuesto

        agg = Repuesto.objects.filter(empresa=empresa).aggregate(
            stock_critical=Count(
                "id",
                filter=Q(cantidad_stock__lte=F("stock_minimo"), stock_minimo__gt=0),
            ),
            inventory_value=Coalesce(
                Sum(F("cantidad_stock") * F("precio_venta")),
                _ZERO_DEC,
            ),
        )
        return {
            WGT_KPI_STOCK_CRITICAL:  agg["stock_critical"],
            WGT_KPI_INVENTORY_VALUE: agg["inventory_value"],
        }

    @staticmethod
    def _query_desarm(empresa) -> dict:
        from taller.models.vehiculo_desarme import VehiculoDesarme

        count = VehiculoDesarme.objects.filter(
            empresa=empresa,
            estado_desarme__in=["INGRESADO", "DESARMANDO"],
            es_placeholder=False,
        ).count()
        return {WGT_KPI_DESARM_AVAIL: count}

    @staticmethod
    def _query_lineas(empresa, month_start: date, next_month_start: date) -> dict:
        from taller.models.lineas_documento import LineaRepuesto, ORIGEN_STOCK_BODEGA

        _DEC = DecimalField(max_digits=18, decimal_places=4)

        base = LineaRepuesto.objects.filter(
            documento__empresa=empresa,
            documento__tipo__in=["OT", "FAC", "PTS"],
            documento__estado="EMITIDO",
            documento__fecha_emision__gte=month_start,
            documento__fecha_emision__lt=next_month_start,
            origen_repuesto=ORIGEN_STOCK_BODEGA,
        )

        ingreso_expr = ExpressionWrapper(
            F("cantidad") * F("precio_unitario") * (Value(Decimal("100")) - F("descuento")) / Value(Decimal("100")),
            output_field=_DEC,
        )
        costo_expr = ExpressionWrapper(
            F("cantidad") * F("costo_linea"),
            output_field=_DEC,
        )

        agg = base.aggregate(
            lineas_total=Count("id"),
            lineas_con_costo=Count("id", filter=Q(costo_linea__isnull=False)),
            ingreso_conocido=Coalesce(
                Sum(ingreso_expr, filter=Q(costo_linea__isnull=False)),
                _ZERO_DEC,
            ),
            costo_conocido=Coalesce(
                Sum(costo_expr, filter=Q(costo_linea__isnull=False)),
                _ZERO_DEC,
            ),
        )

        lineas_total    = agg["lineas_total"] or 0
        lineas_con_costo = agg["lineas_con_costo"] or 0
        ingreso         = agg["ingreso_conocido"]
        costo           = agg["costo_conocido"]

        if lineas_total > 0:
            cobertura = Decimal(lineas_con_costo) / Decimal(lineas_total) * 100
        else:
            cobertura = Decimal("0.00")

        margin = None
        if lineas_total > 0 and cobertura >= MIN_MARGIN_COST_COVERAGE and ingreso > 0:
            margin = (ingreso - costo) / ingreso * 100

        return {
            WGT_KPI_MARGIN_MONTH: {
                "value":     Decimal("0.00") if margin is None else margin,
                "has_value": margin is not None,
            }
        }

    # ------------------------------------------------------------------
    # Widget builder — combines raw values with WIDGET_DEFINITIONS.
    # ------------------------------------------------------------------

    @staticmethod
    def _build_widgets(widget_keys: tuple, raw: dict) -> list:
        widgets = []
        for key in widget_keys:
            defn = WIDGET_DEFINITIONS.get(key, {})
            raw_val = raw.get(key, 0)
            if isinstance(raw_val, dict):
                value     = raw_val.get("value", Decimal("0.00"))
                has_value = raw_val.get("has_value", True)
            else:
                value     = raw_val
                has_value = True
            widgets.append({
                "key":       key,
                "title":     str(defn.get("title", key)),
                "icon":      defn.get("icon", "fas fa-circle"),
                "value":     value,
                "format":    defn.get("format", "number"),
                "has_value": has_value,
            })
        return widgets
