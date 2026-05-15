import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado

FILENAME = "estados_ciudades_usa.json"


def _find_usa_json():
    """Busca el JSON en varias ubicaciones (proyecto, utils hermano, data)."""
    base = Path(settings.BASE_DIR)
    candidates = [
        base / "utils" / FILENAME,
        base / "data" / FILENAME,
        base.parent / "utils" / FILENAME,
        Path(__file__).resolve().parent.parent.parent.parent / "utils" / FILENAME,
        Path(__file__).resolve().parent / ".." / ".." / ".." / "utils" / FILENAME,
    ]
    for p in candidates:
        try:
            p = p.resolve()
            if p.is_file():
                return p
        except (OSError, RuntimeError):
            continue
    return None


class Command(BaseCommand):
    help = "Carga los estados y ciudades de USA desde el JSON (utils/ o data/)."

    def handle(self, *args, **options):
        json_path = _find_usa_json()
        if not json_path or not json_path.is_file():
            self.stdout.write(
                self.style.ERROR(
                    f"No se encontró {FILENAME}. Colócalo en utils/ o data/ del proyecto."
                )
            )
            return
        self.stdout.write(f"Usando: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # Solo borrar si no hay clientes usando estas ciudades
        if Ciudad.objects.count() > 0:
            self.stdout.write(
                self.style.WARNING(
                    "Ya existen ciudades en la BD. Se omitirá el borrado para evitar conflictos."
                )
            )

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
        # Crear estados si no existen
        estados_objs = []
        for estado_nombre in data.keys():
            codigo_estado = state_codes.get(estado_nombre, estado_nombre[:2].upper())
            # Usar get_or_create con pais y codigo para evitar duplicados
            estado, created = Estado.objects.get_or_create(
                pais="US", codigo=codigo_estado, defaults={"nombre": estado_nombre}
            )
            if created:
                estados_creados += 1
            else:
                # Si el estado ya existe pero no tiene el nombre correcto, actualizarlo
                if estado.nombre != estado_nombre:
                    estado.nombre = estado_nombre
                    estado.save()

        # Crear ciudades si no existen (solo estados US para evitar colisiones de nombre)
        estados_dict = {e.nombre: e for e in Estado.objects.filter(pais="US")}
        ciudades_objs = []
        for estado_nombre, ciudades in data.items():
            if estado_nombre in estados_dict:
                estado = estados_dict[estado_nombre]
                for ciudad_nombre in ciudades:
                    ciudad, created = Ciudad.objects.get_or_create(
                        nombre=ciudad_nombre, estado=estado
                    )
                    if created:
                        ciudades_creadas += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Estados creados: {estados_creados}, Ciudades creadas: {ciudades_creadas}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Total estados: {Estado.objects.count()}, Total ciudades: {Ciudad.objects.count()}"
            )
        )
