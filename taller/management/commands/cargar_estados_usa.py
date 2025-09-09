import json
import os

from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga los estados y ciudades de USA desde el JSON."

    def handle(self, *args, **options):
        json_path = os.path.join(
            os.path.dirname(__file__), "../../../utils/estados_ciudades_usa.json"
        )
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        # Borrar datos previos para evitar conflictos de unicidad
        Ciudad.objects.all().delete()
        Estado.objects.all().delete()
        estados_creados = 0
        ciudades_creadas = 0
        # Diccionario de nombre de estado a código oficial
        state_codes = {
            "Alabama": "AL",
            "Alaska": "AK",
            "Arizona": "AZ",
            "Arkansas": "AR",
            "California": "CA",
            "Colorado": "CO",
            "Connecticut": "CT",
            "Delaware": "DE",
            "Florida": "FL",
            "Georgia": "GA",
            "Hawaii": "HI",
            "Idaho": "ID",
            "Illinois": "IL",
            "Indiana": "IN",
            "Iowa": "IA",
            "Kansas": "KS",
            "Kentucky": "KY",
            "Louisiana": "LA",
            "Maine": "ME",
            "Maryland": "MD",
            "Massachusetts": "MA",
            "Michigan": "MI",
            "Minnesota": "MN",
            "Mississippi": "MS",
            "Missouri": "MO",
            "Montana": "MT",
            "Nebraska": "NE",
            "Nevada": "NV",
            "New Hampshire": "NH",
            "New Jersey": "NJ",
            "New Mexico": "NM",
            "New York": "NY",
            "North Carolina": "NC",
            "North Dakota": "ND",
            "Ohio": "OH",
            "Oklahoma": "OK",
            "Oregon": "OR",
            "Pennsylvania": "PA",
            "Rhode Island": "RI",
            "South Carolina": "SC",
            "South Dakota": "SD",
            "Tennessee": "TN",
            "Texas": "TX",
            "Utah": "UT",
            "Vermont": "VT",
            "Virginia": "VA",
            "Washington": "WA",
            "West Virginia": "WV",
            "Wisconsin": "WI",
            "Wyoming": "WY",
        }
        estados_objs = []
        for estado_nombre in data.keys():
            codigo_estado = state_codes.get(estado_nombre, estado_nombre[:2].upper())
            estados_objs.append(Estado(nombre=estado_nombre, codigo=codigo_estado))
        Estado.objects.bulk_create(estados_objs)
        estados_dict = {e.nombre: e for e in Estado.objects.all()}
        ciudades_objs = []
        for estado_nombre, ciudades in data.items():
            estado = estados_dict[estado_nombre]
            for ciudad_nombre in ciudades:
                ciudades_objs.append(Ciudad(nombre=ciudad_nombre, estado=estado))
        Ciudad.objects.bulk_create(ciudades_objs)
        self.stdout.write(
            self.style.SUCCESS(
                f"Estados creados: {len(estados_objs)}, Ciudades creadas: {len(ciudades_objs)}"
            )
        )
