"""Populate a realistic Chilean dismantling yard for support/demo use.

The command is intentionally idempotent: vehicles are keyed by company and
plate, while parts are keyed by company, vehicle and code. Running it again
refreshes the demo values without creating duplicates.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from taller.models.compatibility import PartApplication
from taller.models.empresa import Empresa
from taller.models.pieza_desarme import (
    ESTADO_DANADA,
    ESTADO_DISPONIBLE,
    ESTADO_FALTANTE,
    ESTADO_VENDIDA,
    PiezaDesarme,
)
from taller.models.vehiculo_desarme import VehiculoDesarme


VEHICLES = [
    ("Toyota", "Hilux 2.4 D-4D", 2019, "pickup", 4, "Patio Fila A - Lote 01", "HIL-2019-01"),
    ("Nissan", "Versa 1.6 Sense", 2018, "sedan", 4, "Patio Fila A - Lote 02", "VER-2018-02"),
    ("Chevrolet", "Sail 1.5 Classic", 2017, "sedan", 4, "Patio Fila A - Lote 03", "SAI-2017-03"),
    ("Hyundai", "Accent 1.4 GL", 2016, "sedan", 4, "Patio Fila B - Lote 01", "ACC-2016-04"),
    ("Kia", "Rio 5 1.4 EX", 2019, "hatchback", 5, "Patio Fila B - Lote 02", "RIO-2019-05"),
    ("Suzuki", "Swift 1.2 GLX", 2020, "hatchback", 5, "Patio Fila B - Lote 03", "SWI-2020-06"),
    ("Mitsubishi", "L200 2.5 Work", 2015, "pickup", 2, "Patio Fila C - Lote 01", "L20-2015-07"),
    ("Peugeot", "208 1.6 BlueHDi", 2018, "hatchback", 5, "Patio Fila C - Lote 02", "208-2018-08"),
    ("Ford", "Ranger 3.2 XLT 4x4", 2017, "pickup", 4, "Patio Fila C - Lote 03", "RAN-2017-09"),
    ("Kia", "Grand Carnival 2.2 CRDi", 2016, "van", 5, "Patio Fila D - Lote 01", "CAR-2016-10"),
]


PART_BLUEPRINT = (
    ("ALT", "Alternador 90A", "engine.alternator", 125000, "VEHICULO", ESTADO_DISPONIBLE),
    ("MOT", "Motor de Partida", "engine.starter", 145000, "VEHICULO", ESTADO_DISPONIBLE),
    ("RAD", "Radiador de Agua", "cooling.radiator", 95000, "VEHICULO", ESTADO_DISPONIBLE),
    ("PUERTA-DEL-IZQ", "Puerta Delantera Izquierda", "door.front.left", 110000, "VEHICULO", ESTADO_DISPONIBLE),
    ("PUERTA-DEL-DER", "Puerta Delantera Derecha", "door.front.right", 110000, "VEHICULO", ESTADO_DISPONIBLE),
    ("CUE", "Cuerpo de Aceleración", "engine.throttle_body", 85000, "BODEGA", ESTADO_DISPONIBLE),
    ("ECU", "Computador de Motor ECU", "engine.ecu", 175000, "BODEGA", ESTADO_DISPONIBLE),
    ("FOCO", "Óptico Delantero Izquierdo", "front.light.left", 65000, "BODEGA", ESTADO_VENDIDA),
    ("PAR", "Parachoques Delantero", "body.front.bumper", 90000, "VEHICULO", ESTADO_DANADA),
)


class Command(BaseCommand):
    help = "Puebla Atlanta Desarmaduría con 10 vehículos, piezas, slots e interchange."

    def add_arguments(self, parser):
        parser.add_argument("--empresa-id", type=int, default=None)
        parser.add_argument("--dry-run", action="store_true")

    def _get_empresa(self, empresa_id):
        if empresa_id:
            try:
                return Empresa.objects.get(pk=empresa_id)
            except Empresa.DoesNotExist as exc:
                raise CommandError(f"No existe la Empresa {empresa_id}") from exc

        empresa = Empresa.objects.filter(nombre_taller__icontains="Atlanta Desarmaduría").first()
        if empresa:
            return empresa

        config = Empresa.objects.filter(config__rubro_principal="DESARMADURIA").first()
        if config:
            return config

        raise CommandError("No se encontró una Empresa con rubro DESARMADURIA")

    @staticmethod
    def _plate(index):
        return f"DEMO{index:02d}"

    @staticmethod
    def _piece_state(piece_index):
        """Return location/state for the 9-piece distribution per vehicle."""
        if piece_index <= 4:
            return "VEHICULO", ESTADO_DISPONIBLE, 1, True
        if piece_index <= 6:
            return "BODEGA", ESTADO_DISPONIBLE, 1, True
        if piece_index == 7:
            return "BODEGA", ESTADO_VENDIDA, 0, False
        return "VEHICULO", ESTADO_DANADA, 1, False

    @transaction.atomic
    def handle(self, *args, **options):
        empresa = self._get_empresa(options.get("empresa_id"))
        if options["dry_run"]:
            self.stdout.write(f"DRY_RUN empresa_id={empresa.id} nombre={empresa.nombre_taller}")
            return

        vehicles_created = 0
        parts_created = 0
        applications_created = 0
        today = date.today()
        vehicle_rows = []

        for index, (brand, model, year, body, doors, yard_location, code) in enumerate(VEHICLES, start=1):
            vehicle, created = VehiculoDesarme.objects.update_or_create(
                empresa=empresa,
                patente=self._plate(index),
                defaults={
                    "marca_texto": brand,
                    "modelo_texto": model,
                    "anio": year,
                    "numero_puertas": doors,
                    "tipo_carroceria": body,
                    "ubicacion_fisica": yard_location,
                    "estado_desarme": "DESARMANDO",
                    "estado_operativo": "EN_PROCESAMIENTO",
                    "fecha_ingreso_desarme": today - timedelta(days=index * 3),
                    "precio_compra": Decimal(1700000 + index * 85000),
                    "observaciones_desarme": "Vehículo demo de patio para pruebas del gemelo digital.",
                },
            )
            vehicles_created += int(created)
            vehicle_rows.append((vehicle, code, brand, model, year))

            for piece_index, (prefix, name, slot, price, default_location, default_state) in enumerate(
                PART_BLUEPRINT, start=1
            ):
                location, state, quantity, active = self._piece_state(piece_index)
                # Keep the requested four mounted pieces in the patio. Extracted
                # pieces carry an extraction date and therefore belong in storage.
                extraction_date = None if location == "VEHICULO" else today - timedelta(days=index)
                physical_location = (
                    yard_location if location == "VEHICULO" else f"Estante {chr(64 + index)}-{piece_index}, Repisa 3"
                )
                piece_code = f"{prefix}-{code}"
                defaults = {
                    "nombre": f"{name} {brand} {model.split()[0]}",
                    "cantidad": quantity,
                    "costo_asignado": Decimal(int(price * 0.42)),
                    "precio_venta_sugerido": Decimal(price),
                    "precio_referencia": Decimal(price),
                    "precio_sugerido": Decimal(price),
                    "origen_precio": "MANUAL",
                    "prioridad": 5 if prefix in {"ALT", "MOT", "RAD"} else 2,
                    "revisado": True,
                    "fecha_extraccion": extraction_date,
                    "activo": active,
                    "publicada": active and state == ESTADO_DISPONIBLE,
                    "estado_pieza": state,
                    "condicion": "REGULAR" if state == ESTADO_DANADA else "BUENA",
                    "ubicacion_fisica": physical_location,
                    "ubicacion_tipo": location,
                    "visual_slot": slot,
                    "origen": "DESARME_PROPIO",
                    "observaciones": "Pieza demo para pruebas de inventario y mapa visual.",
                }
                _, created = PiezaDesarme.objects.update_or_create(
                    empresa=empresa,
                    vehiculo_desarme=vehicle,
                    codigo=piece_code,
                    defaults=defaults,
                )
                parts_created += int(created)

        applications = [
            ("ALT-HIL-2019-01", "Toyota", "Yaris", 2015, 2020),
            ("ALT-HIL-2019-01", "Nissan", "Versa", 2016, 2020),
            ("ALT-HIL-2019-01", "Suzuki", "Swift", 2017, 2021),
            ("MOT-HIL-2019-01", "Chevrolet", "Sail", 2015, 2019),
            ("MOT-HIL-2019-01", "Hyundai", "Accent", 2014, 2019),
        ]
        for code, brand, model, year_from, year_to in applications:
            _, created = PartApplication.objects.get_or_create(
                codigo_pieza=code,
                marca=brand,
                modelo=model,
                anio_desde=year_from,
                anio_hasta=year_to,
                defaults={
                    "fuente": "demo_desarme_yard",
                    "nivel_confianza": 5,
                    "activo": True,
                },
            )
            applications_created += int(created)

        total_parts = PiezaDesarme.objects.filter(empresa=empresa).count()
        total_vehicles = VehiculoDesarme.objects.filter(empresa=empresa).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"OK empresa_id={empresa.id} vehiculos_creados={vehicles_created} "
                f"vehiculos_total={total_vehicles} piezas_creadas={parts_created} "
                f"piezas_total={total_parts} interchange_creados={applications_created}"
            )
        )
