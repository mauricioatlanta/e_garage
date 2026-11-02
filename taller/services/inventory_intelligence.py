from __future__ import annotations

import math
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Max, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from taller.models.lineas_documento import ORIGEN_STOCK_BODEGA, LineaRepuesto
from taller.models.repuesto import Repuesto


class InventoryIntelligenceService:
    DEFAULT_LOOKBACK_DAYS = 30
    DEFAULT_TARGET_COVERAGE_DAYS = 30
    CRITICAL_COVERAGE_DAYS = 7

    @classmethod
    def calculate_days_coverage(cls, stock_actual, consumo_diario):
        stock = Decimal(str(stock_actual or 0))
        daily = Decimal(str(consumo_diario or 0))
        if daily <= 0:
            return None
        return (stock / daily).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_purchase_suggestion(
        cls,
        stock_actual,
        consumo_diario,
        stock_minimo=0,
        target_coverage_days=None,
    ) -> int:
        target_days = int(target_coverage_days or cls.DEFAULT_TARGET_COVERAGE_DAYS)
        stock = int(stock_actual or 0)
        minimo = int(stock_minimo or 0)
        daily = Decimal(str(consumo_diario or 0))

        stock_objetivo = minimo
        if daily > 0:
            stock_objetivo = max(stock_objetivo, int(math.ceil(float(daily * target_days))))

        return max(stock_objetivo - stock, 0)

    @classmethod
    def build_repuesto_snapshot(
        cls,
        repuesto: Repuesto,
        consumo_total=0,
        ultimo_consumo=None,
        lookback_days=None,
        target_coverage_days=None,
    ):
        window_days = max(int(lookback_days or cls.DEFAULT_LOOKBACK_DAYS), 1)
        target_days = int(target_coverage_days or cls.DEFAULT_TARGET_COVERAGE_DAYS)
        total = Decimal(str(consumo_total or 0))
        consumo_diario = (total / Decimal(window_days)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        stock_actual = int(repuesto.cantidad_stock or 0)
        stock_minimo = int(repuesto.stock_minimo or 0)
        dias_cobertura = cls.calculate_days_coverage(stock_actual, consumo_diario)
        sugerencia_compra = cls.calculate_purchase_suggestion(
            stock_actual=stock_actual,
            consumo_diario=consumo_diario,
            stock_minimo=stock_minimo,
            target_coverage_days=target_days,
        )

        if sugerencia_compra > 0 and (
            stock_actual <= 0
            or (dias_cobertura is not None and dias_cobertura < cls.CRITICAL_COVERAGE_DAYS)
            or (stock_minimo and stock_actual < stock_minimo)
        ):
            status = "critical"
        elif sugerencia_compra > 0:
            status = "warning"
        elif consumo_diario > 0:
            status = "stable"
        else:
            status = "idle"

        return {
            "repuesto": repuesto,
            "consumo_total": total,
            "consumo_diario": consumo_diario,
            "dias_cobertura": dias_cobertura,
            "sugerencia_compra": sugerencia_compra,
            "stock_actual": stock_actual,
            "stock_minimo": stock_minimo,
            "ultimo_consumo": ultimo_consumo,
            "status": status,
            "target_coverage_days": target_days,
        }

    @classmethod
    def _build_consumption_map(cls, empresa, start_date):
        rows = (
            LineaRepuesto.objects.filter(
                documento__empresa=empresa,
                documento__estado="EMITIDO",
                documento__fecha_emision__gte=start_date,
                origen_repuesto=ORIGEN_STOCK_BODEGA,
                repuesto_id__isnull=False,
            )
            .values("repuesto_id")
            .annotate(
                consumo_total=Coalesce(Sum("cantidad"), Value(0)),
                ultimo_consumo=Max("documento__fecha_emision"),
            )
        )
        return {row["repuesto_id"]: row for row in rows}

    @classmethod
    def build_panel(
        cls,
        empresa,
        queryset=None,
        lookback_days=None,
        target_coverage_days=None,
    ):
        if not empresa:
            return {
                "rows": [],
                "summary": {
                    "total_repuestos": 0,
                    "critical_count": 0,
                    "warning_count": 0,
                    "suggested_units": 0,
                },
                "lookback_days": int(lookback_days or cls.DEFAULT_LOOKBACK_DAYS),
                "target_coverage_days": int(
                    target_coverage_days or cls.DEFAULT_TARGET_COVERAGE_DAYS
                ),
            }

        window_days = max(int(lookback_days or cls.DEFAULT_LOOKBACK_DAYS), 1)
        target_days = int(target_coverage_days or cls.DEFAULT_TARGET_COVERAGE_DAYS)
        start_date = timezone.localdate() - timedelta(days=window_days - 1)
        repuestos = queryset if queryset is not None else Repuesto.objects.filter(empresa=empresa)
        consumo_map = cls._build_consumption_map(empresa, start_date)

        rows = []
        for repuesto in repuestos:
            metrics = consumo_map.get(repuesto.pk, {})
            rows.append(
                cls.build_repuesto_snapshot(
                    repuesto=repuesto,
                    consumo_total=metrics.get("consumo_total", 0),
                    ultimo_consumo=metrics.get("ultimo_consumo"),
                    lookback_days=window_days,
                    target_coverage_days=target_days,
                )
            )

        rows.sort(
            key=lambda row: (
                {"critical": 0, "warning": 1, "stable": 2, "idle": 3}[row["status"]],
                -row["sugerencia_compra"],
                row["repuesto"].nombre.lower(),
            )
        )

        return {
            "rows": rows,
            "summary": {
                "total_repuestos": len(rows),
                "critical_count": sum(1 for row in rows if row["status"] == "critical"),
                "warning_count": sum(1 for row in rows if row["status"] == "warning"),
                "suggested_units": sum(row["sugerencia_compra"] for row in rows),
            },
            "lookback_days": window_days,
            "target_coverage_days": target_days,
        }
