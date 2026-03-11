"""
Seed inicial de plantillas de desarme globales (empresa=null).
Crea: Sedan, SUV, Pickup, Hatchback, Manual (vacía).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models import PlantillaDesarme, PlantillaPieza


PLANTILLAS_BASE = [
    {
        "nombre": "Sedan",
        "descripcion": "Sedán compacto/mediano típico",
        "piezas": [
            ("Motor", "", "", ""),
            ("Caja", "", "", ""),
            ("Alternador", "", "", ""),
            ("Radiador", "", "", ""),
            ("Compresor AC", "", "", ""),
            ("ECU", "", "", ""),
            ("Catalítico", "", "", ""),
            ("Capot", "hood", "frontal", ""),
            ("Parachoques delantero", "front_bumper", "frontal", ""),
            ("Parachoques trasero", "rear_bumper", "lateral_izq", ""),
            ("Foco delantero izquierdo", "front_left_headlight", "frontal", "left"),
            ("Foco delantero derecho", "front_right_headlight", "frontal", "right"),
            ("Foco trasero izquierdo", "left_taillight", "lateral_izq", "left"),
            ("Foco trasero derecho", "", "", "right"),
            ("Espejo izquierdo", "left_mirror", "lateral_izq", "left"),
            ("Espejo derecho", "", "", "right"),
            ("Puerta delantera izquierda", "left_front_door", "lateral_izq", "left"),
            ("Puerta delantera derecha", "", "", "right"),
            ("Puerta trasera izquierda", "left_rear_door", "lateral_izq", "left"),
            ("Puerta trasera derecha", "", "", "right"),
            ("Maleta", "trunk", "lateral_izq", ""),
            ("Llanta delantera izquierda", "left_front_wheel", "lateral_izq", "left"),
            ("Llanta delantera derecha", "", "", "right"),
            ("Llanta trasera izquierda", "left_rear_wheel", "lateral_izq", "left"),
            ("Llanta trasera derecha", "", "", "right"),
        ],
    },
    {
        "nombre": "SUV",
        "descripcion": "SUV / 4x4",
        "piezas": [
            ("Motor", "", "", ""),
            ("Caja", "", "", ""),
            ("Transfer", "", "", ""),
            ("Alternador", "", "", ""),
            ("Compresor AC", "", "", ""),
            ("Radiador", "", "", ""),
            ("Capot", "hood", "frontal", ""),
            ("Maleta", "trunk", "lateral_izq", ""),
            ("Puerta delantera izquierda", "left_front_door", "lateral_izq", "left"),
            ("Puerta delantera derecha", "", "", "right"),
            ("Puerta trasera izquierda", "left_rear_door", "lateral_izq", "left"),
            ("Puerta trasera derecha", "", "", "right"),
            ("Foco delantero izquierdo", "front_left_headlight", "frontal", "left"),
            ("Foco delantero derecho", "front_right_headlight", "frontal", "right"),
            ("Foco trasero izquierdo", "left_taillight", "lateral_izq", "left"),
            ("Foco trasero derecho", "", "", "right"),
            ("Parachoques delantero", "front_bumper", "frontal", ""),
            ("Parachoques trasero", "rear_bumper", "lateral_izq", ""),
            ("Portón trasero", "", "", ""),
            ("Catalítico", "", "", ""),
            ("ECU", "", "", ""),
        ],
    },
    {
        "nombre": "Pickup",
        "descripcion": "Pickup / Camioneta",
        "piezas": [
            ("Motor", "", "", ""),
            ("Caja", "", "", ""),
            ("Alternador", "", "", ""),
            ("Compresor AC", "", "", ""),
            ("Radiador", "", "", ""),
            ("Capot", "hood", "frontal", ""),
            ("Puerta izquierda", "left_front_door", "lateral_izq", "left"),
            ("Puerta derecha", "", "", "right"),
            ("Foco delantero izquierdo", "front_left_headlight", "frontal", "left"),
            ("Foco delantero derecho", "front_right_headlight", "frontal", "right"),
            ("Foco trasero izquierdo", "left_taillight", "lateral_izq", "left"),
            ("Foco trasero derecho", "", "", "right"),
            ("Parachoques delantero", "front_bumper", "frontal", ""),
            ("Parachoques trasero", "rear_bumper", "lateral_izq", ""),
            ("Catalítico", "", "", ""),
            ("ECU", "", "", ""),
            ("Cabina", "", "", ""),
        ],
    },
    {
        "nombre": "Hatchback",
        "descripcion": "Hatchback compacto",
        "piezas": [
            ("Motor", "", "", ""),
            ("Caja", "", "", ""),
            ("Alternador", "", "", ""),
            ("Compresor AC", "", "", ""),
            ("Radiador", "", "", ""),
            ("Capot", "hood", "frontal", ""),
            ("Portón trasero", "trunk", "lateral_izq", ""),
            ("Puerta delantera izquierda", "left_front_door", "lateral_izq", "left"),
            ("Puerta delantera derecha", "", "", "right"),
            ("Puerta trasera izquierda", "left_rear_door", "lateral_izq", "left"),
            ("Puerta trasera derecha", "", "", "right"),
            ("Foco delantero izquierdo", "front_left_headlight", "frontal", "left"),
            ("Foco delantero derecho", "front_right_headlight", "frontal", "right"),
            ("Foco trasero izquierdo", "left_taillight", "lateral_izq", "left"),
            ("Foco trasero derecho", "", "", "right"),
            ("Parachoques delantero", "front_bumper", "frontal", ""),
            ("Parachoques trasero", "rear_bumper", "lateral_izq", ""),
            ("Catalítico", "", "", ""),
            ("ECU", "", "", ""),
        ],
    },
    {
        "nombre": "Manual",
        "descripcion": "Plantilla vacía para agregar piezas manualmente",
        "piezas": [],
    },
]


class Command(BaseCommand):
    help = "Crea plantillas de desarme globales: Sedan, SUV, Pickup, Hatchback, Manual"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recrear aunque ya existan plantillas globales",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options.get("force", False)

        if not force and PlantillaDesarme.objects.filter(empresa__isnull=True).exists():
            self.stdout.write(
                self.style.WARNING("Ya existen plantillas globales. Use --force para recrear.")
            )
            return

        if force:
            PlantillaDesarme.objects.filter(empresa__isnull=True).delete()

        created = 0
        for data in PLANTILLAS_BASE:
            plantilla = PlantillaDesarme.objects.filter(
                nombre=data["nombre"], empresa__isnull=True
            ).first()
            if not plantilla:
                plantilla = PlantillaDesarme.objects.create(
                    nombre=data["nombre"],
                    empresa=None,
                    descripcion=data["descripcion"],
                    activa=True,
                )
                created += 1

            for orden, item in enumerate(data["piezas"], start=1):
                if isinstance(item, (list, tuple)):
                    nombre_pieza, zona_mapa, vista_mapa, lado = (item + ("", "", "", ""))[:4]
                else:
                    nombre_pieza, zona_mapa, vista_mapa, lado = item, "", "", ""
                PlantillaPieza.objects.get_or_create(
                    plantilla=plantilla,
                    nombre_pieza=nombre_pieza,
                    defaults={
                        "orden": orden,
                        "activo": True,
                        "zona_mapa": zona_mapa or "",
                        "vista_mapa": vista_mapa or "",
                        "lado": lado or "",
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Plantillas de desarme creadas: {len(PLANTILLAS_BASE)} " f"(nuevas: {created})"
            )
        )
