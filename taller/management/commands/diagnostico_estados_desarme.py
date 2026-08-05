"""
Diagnóstico de estados operativos de VehiculoDesarme.

Solo lectura. No modifica datos.

Uso:
    python manage.py diagnostico_estados_desarme
    python manage.py diagnostico_estados_desarme --empresa-id 42
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q


class Command(BaseCommand):
    help = "Diagnóstico de estado_operativo en VehiculoDesarme. Solo lectura."

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa-id",
            type=int,
            default=None,
            metavar="ID",
            help="Filtrar por empresa específica (omitir = todas las empresas).",
        )

    def handle(self, *args, **options):
        from taller.models.vehiculo_desarme import VehiculoDesarme
        from taller.models.vehiculo_desarme_event import VehiculoDesarmeEvent

        empresa_id = options.get("empresa_id")
        qs = VehiculoDesarme.objects.all()
        ev_qs = VehiculoDesarmeEvent.objects.all()
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
            ev_qs = ev_qs.filter(empresa_id=empresa_id)

        sep = "─" * 58
        self.stdout.write(f"\n{sep}")
        self.stdout.write("  DIAGNÓSTICO: estados operativos de desarme")
        if empresa_id:
            self.stdout.write(f"  Empresa filtrada: {empresa_id}")
        self.stdout.write(sep)

        total = qs.count()
        self.stdout.write(f"\n  Vehículos totales:              {total:>8,}")

        # ── Por estado_desarme legacy ─────────────────────────────────────
        self.stdout.write(f"\n  {'Por estado_desarme (legacy)':─<50}")
        for row in qs.values("estado_desarme").annotate(n=Count("id")).order_by("-n"):
            label = row["estado_desarme"] or "(nulo/vacío)"
            self.stdout.write(f"    {label:<30} {row['n']:>6,}")

        # ── Por estado_operativo ──────────────────────────────────────────
        self.stdout.write(f"\n  {'Por estado_operativo':─<50}")
        for row in qs.values("estado_operativo").annotate(n=Count("id")).order_by("-n"):
            self.stdout.write(f"    {row['estado_operativo']:<30} {row['n']:>6,}")

        # ── Actividad operacional ─────────────────────────────────────────
        con_piezas = qs.filter(piezas_desarme__activo=True).distinct().count()
        con_publicadas = qs.filter(
            piezas_desarme__activo=True, piezas_desarme__publicada=True
        ).distinct().count()
        con_sugerencias = qs.filter(
            sugerencias_piezas__estado="PENDIENTE"
        ).distinct().count()
        con_ventas = qs.filter(
            piezas_desarme__lineas_venta_desarme__isnull=False
        ).distinct().count()
        veh_con_eventos = set(
            ev_qs.values_list("vehiculo_id", flat=True).distinct()
        )
        sin_eventos = qs.exclude(id__in=veh_con_eventos).count()

        self.stdout.write(f"\n  {'Actividad operacional':─<50}")
        self.stdout.write(f"    Con piezas activas:            {con_piezas:>6,}")
        self.stdout.write(f"    Con piezas publicadas:         {con_publicadas:>6,}")
        self.stdout.write(f"    Con sugerencias pendientes:    {con_sugerencias:>6,}")
        self.stdout.write(f"    Con ventas registradas:        {con_ventas:>6,}")
        self.stdout.write(f"    Sin ningún evento operacional: {sin_eventos:>6,}")

        # ── Eventos por tipo ──────────────────────────────────────────────
        self.stdout.write(f"\n  {'Eventos por tipo':─<50}")
        total_eventos = 0
        for row in ev_qs.values("tipo").annotate(n=Count("id")).order_by("-n"):
            self.stdout.write(f"    {row['tipo']:<40} {row['n']:>6,}")
            total_eventos += row["n"]
        self.stdout.write(f"    {'TOTAL':─<40} {total_eventos:>6,}")

        # ── Inconsistencias ───────────────────────────────────────────────
        self.stdout.write(f"\n  {'Inconsistencias detectadas':─<50}")
        inconsistencias = 0

        # Cerrado en legacy pero no en estado_operativo
        cerrado_legacy_mal = qs.filter(
            estado_desarme__in=["CERRADO", "BAJA", "AGOTADO"],
        ).exclude(estado_operativo="CERRADO").count()
        if cerrado_legacy_mal:
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ {cerrado_legacy_mal} veh. cerrados legacy con estado_operativo != CERRADO"
                )
            )
            inconsistencias += cerrado_legacy_mal

        # En estado avanzado sin piezas ni sugerencias
        sin_datos_avanzados = qs.filter(
            estado_operativo__in=["EN_REVISION", "EN_PROCESAMIENTO"],
            piezas_desarme__isnull=True,
            sugerencias_piezas__isnull=True,
        ).distinct().count()
        if sin_datos_avanzados:
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ {sin_datos_avanzados} veh. en EN_REVISION/EN_PROCESAMIENTO "
                    "sin piezas ni sugerencias"
                )
            )
            inconsistencias += sin_datos_avanzados

        # Eventos con empresa diferente a la del vehículo (corrupción de tenant)
        ev_empresa_distinta = (
            VehiculoDesarmeEvent.objects
            .filter(vehiculo__isnull=False)
            .exclude(empresa=F("vehiculo__empresa"))
            .count()
        )
        if ev_empresa_distinta:
            self.stdout.write(
                self.style.ERROR(
                    f"    ✗ {ev_empresa_distinta} eventos con empresa distinta al vehículo"
                )
            )
            inconsistencias += ev_empresa_distinta

        if inconsistencias == 0:
            self.stdout.write(self.style.SUCCESS("    ✓ Sin inconsistencias detectadas."))

        self.stdout.write(f"\n{sep}\n")
