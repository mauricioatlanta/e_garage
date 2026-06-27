from decimal import Decimal

from django.utils import timezone

from taller.models.vehiculo_financial import VehiculoFinancialSnapshot
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.services.desarme_financial_service import (
    calcular_costo_vendido_vehiculo,
    calcular_ganancia_vehiculo,
    calcular_ingresos_vehiculo,
    calcular_inventario_vivo_vehiculo,
    calcular_inversion_total_vehiculo,
    calcular_recuperacion_vehiculo,
    calcular_roi_vehiculo,
    calcular_dias_recuperacion,
)
from taller.services.desarme_kpi_service import health_score


class SnapshotGeneratorService:
    """Servicio para generar snapshots financieros de vehículos de desarme."""

    @classmethod
    def generate_snapshot_for_vehicle(cls, vehiculo: VehiculoDesarme, fecha=None) -> VehiculoFinancialSnapshot:
        fecha = fecha or timezone.now()
        inventario = calcular_inventario_vivo_vehiculo(vehiculo)
        inversion_total = calcular_inversion_total_vehiculo(vehiculo)
        ingresos_total = calcular_ingresos_vehiculo(vehiculo)
        costo_vendido = calcular_costo_vendido_vehiculo(vehiculo)
        ganancia = calcular_ganancia_vehiculo(vehiculo)
        roi_pct = calcular_roi_vehiculo(vehiculo)
        recuperacion_pct = calcular_recuperacion_vehiculo(vehiculo)
        dias_recuperacion = calcular_dias_recuperacion(vehiculo)
        health = health_score(vehiculo)

        from taller.models.vehiculo_financial import VehicleFinancialEvent

        source_event_count = VehicleFinancialEvent.objects.filter(
            vehiculo_desarme=vehiculo
        ).count()

        snapshot_hash = "|".join([
            "SNAPSHOT_V1",
            str(vehiculo.id),
            str(source_event_count),
            str(inversion_total),
            str(ingresos_total),
            str(ganancia),
            str(roi_pct),
        ])

        existing = VehiculoFinancialSnapshot.objects.filter(
            snapshot_hash=snapshot_hash
        ).first()

        if existing:
            return existing

        snapshot = VehiculoFinancialSnapshot.objects.create(
            vehiculo_desarme=vehiculo,
            empresa=vehiculo.empresa,
            fecha=fecha,
            inversion_total=inversion_total,
            ingresos_total=ingresos_total,
            costo_vendido=costo_vendido,
            ganancia=ganancia,
            roi_pct=roi_pct,
            recuperacion_pct=recuperacion_pct,
            inventario_contable=inventario.get("valor_contable", Decimal("0.00")),
            inventario_mercado=inventario.get("valor_mercado", Decimal("0.00")),
            dias_recuperacion=dias_recuperacion,
            health_score=Decimal(str(health or 0)),
            source_event_count=source_event_count,
            snapshot_hash=snapshot_hash,
        )

        return snapshot

    @classmethod
    def generate_snapshots_for_empresa(cls, empresa, fecha=None):
        fecha = fecha or timezone.now()
        vehiculos = VehiculoDesarme.objects.filter(empresa=empresa)
        snapshots = []
        for vehiculo in vehiculos:
            snapshots.append(cls.generate_snapshot_for_vehicle(vehiculo, fecha=fecha))
        return snapshots

    @classmethod
    def generate_snapshot_for_document(cls, documento):
        vehiculos = cls._vehiculos_from_documento(documento)
        snapshots = []
        for vehiculo in vehiculos:
            snapshots.append(cls.generate_snapshot_for_vehicle(vehiculo))
        return snapshots

    @classmethod
    def _vehiculos_from_documento(cls, documento):
        return VehiculoDesarme.objects.filter(
            piezas_desarme__lineas_repuesto__documento=documento,
            piezas_desarme__lineas_repuesto__origen_repuesto="DESARME",
        ).distinct()
