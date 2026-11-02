from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from taller.models.extras_vehiculo import (
    CajaVehiculo,
    CajaVehiculoEmpresa,
    MotorVehiculo,
    MotorVehiculoEmpresa,
)
from taller.models.vehiculos import Vehiculo


class Command(BaseCommand):
    help = (
        "Detecta motores/cajas globales usados por una sola empresa y, con --apply, "
        "los migra a catálogos privados por empresa/modelo."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Aplicar cambios. Por defecto solo reporta.")
        parser.add_argument("--empresa-id", type=int, help="Limitar análisis a una empresa.")
        parser.add_argument(
            "--kind",
            choices=("motor", "caja", "all"),
            default="all",
            help="Tipo de catálogo a analizar.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Máximo de vehículos a actualizar por tipo. 0 = sin límite.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        empresa_id = options.get("empresa_id")
        kind = options["kind"]
        limit = options["limit"]

        if not apply:
            self.stdout.write(self.style.WARNING("DRY-RUN: no se modificarán datos. Usa --apply para ejecutar."))

        missing = self._missing_private_schema()
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    "Backfill omitido: faltan columnas/tablas de la migración privada "
                    f"({', '.join(missing)}). Ejecuta migrate antes de analizar/aplicar."
                )
            )
            return

        totals = {"motor": 0, "caja": 0}

        if kind in ("motor", "all"):
            totals["motor"] = self._process_catalog(
                label="motor",
                global_model=MotorVehiculo,
                private_model=MotorVehiculoEmpresa,
                vehicle_global_field="motor",
                vehicle_private_field="motor_empresa",
                empresa_id=empresa_id,
                apply=apply,
                limit=limit,
            )

        if kind in ("caja", "all"):
            totals["caja"] = self._process_catalog(
                label="caja",
                global_model=CajaVehiculo,
                private_model=CajaVehiculoEmpresa,
                vehicle_global_field="caja",
                vehicle_private_field="caja_empresa",
                empresa_id=empresa_id,
                apply=apply,
                limit=limit,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Completado. Vehículos candidatos/procesados: motores={totals['motor']}, cajas={totals['caja']}"
            )
        )

    def _missing_private_schema(self):
        table_names = set(connection.introspection.table_names())
        missing = []
        if "taller_motorvehiculoempresa" not in table_names:
            missing.append("taller_motorvehiculoempresa")
        if "taller_cajavehiculoempresa" not in table_names:
            missing.append("taller_cajavehiculoempresa")

        if "taller_vehiculo" in table_names:
            with connection.cursor() as cursor:
                columns = {
                    col.name
                    for col in connection.introspection.get_table_description(
                        cursor, "taller_vehiculo"
                    )
                }
            for column in ("motor_empresa_id", "caja_empresa_id"):
                if column not in columns:
                    missing.append(f"taller_vehiculo.{column}")

        return missing

    def _process_catalog(
        self,
        *,
        label,
        global_model,
        private_model,
        vehicle_global_field,
        vehicle_private_field,
        empresa_id,
        apply,
        limit,
    ):
        qs = (
            Vehiculo.objects.filter(
                **{
                    f"{vehicle_global_field}__isnull": False,
                    f"{vehicle_private_field}__isnull": True,
                    "empresa__isnull": False,
                    "modelo__isnull": False,
                }
            )
            .select_related("empresa", "modelo", vehicle_global_field)
            .order_by("id")
        )
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        by_global = defaultdict(set)
        for row in qs.values("id", "empresa_id", f"{vehicle_global_field}_id"):
            by_global[row[f"{vehicle_global_field}_id"]].add(row["empresa_id"])

        candidate_ids = [
            global_id for global_id, empresa_ids in by_global.items() if len(empresa_ids) == 1
        ]
        if not candidate_ids:
            self.stdout.write(f"[{label}] Sin candidatos de una sola empresa.")
            return 0

        candidate_qs = qs.filter(**{f"{vehicle_global_field}_id__in": candidate_ids})
        if limit:
            candidate_ids_limited = list(candidate_qs.values_list("id", flat=True)[:limit])
            candidate_qs = candidate_qs.filter(id__in=candidate_ids_limited)

        count = candidate_qs.count()
        self.stdout.write(f"[{label}] {count} vehículos candidatos en {len(candidate_ids)} valores globales.")

        examples = list(candidate_qs[:10])
        for vehicle in examples:
            global_obj = getattr(vehicle, vehicle_global_field)
            self.stdout.write(
                f"  - Vehículo {vehicle.id}: empresa={vehicle.empresa_id}, modelo={vehicle.modelo_id}, "
                f"{label}='{global_obj.nombre}'"
            )

        if not apply:
            return count

        with transaction.atomic():
            updated = 0
            for vehicle in candidate_qs.select_for_update():
                global_obj = getattr(vehicle, vehicle_global_field)
                country = (
                    getattr(global_obj, "country", None)
                    or getattr(vehicle.modelo, "country", None)
                    or getattr(vehicle.empresa, "pais", None)
                    or "CL"
                )
                private_obj, _ = private_model.objects.get_or_create(
                    empresa=vehicle.empresa,
                    modelo=vehicle.modelo,
                    country=str(country).upper()[:2],
                    nombre=global_obj.nombre,
                )
                setattr(vehicle, vehicle_private_field, private_obj)
                setattr(vehicle, vehicle_global_field, None)
                vehicle.save(update_fields=[vehicle_private_field, vehicle_global_field])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"[{label}] Actualizados {updated} vehículos."))
        return updated
