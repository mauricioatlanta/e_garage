import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from taller.models.region_ciudad import TallerCiudad, TallerRegion

# Datos embebidos por si no existe el JSON en el servidor (ej. deploy sin carpeta data/)
REGIONES_CHILE_EMBED = [
    {"region": "Arica y Parinacota", "ciudades": ["Arica", "Putre", "Camarones", "General Lagos"]},
    {
        "region": "Tarapacá",
        "ciudades": ["Iquique", "Alto Hospicio", "Pozo Almonte", "Pica", "Huara"],
    },
    {
        "region": "Antofagasta",
        "ciudades": ["Antofagasta", "Calama", "Tocopilla", "Mejillones", "Taltal"],
    },
    {
        "region": "Atacama",
        "ciudades": ["Copiapó", "Vallenar", "Caldera", "Chañaral", "El Salvador"],
    },
    {"region": "Coquimbo", "ciudades": ["La Serena", "Coquimbo", "Ovalle", "Illapel", "Vicuña"]},
    {
        "region": "Valparaíso",
        "ciudades": ["Valparaíso", "Viña del Mar", "San Antonio", "Quilpué", "Villa Alemana"],
    },
    {
        "region": "Región Metropolitana",
        "ciudades": ["Santiago", "Puente Alto", "Maipú", "La Florida", "Ñuñoa"],
    },
    {
        "region": "O'Higgins",
        "ciudades": ["Rancagua", "San Fernando", "Rengo", "Santa Cruz", "Machalí"],
    },
    {"region": "Maule", "ciudades": ["Talca", "Curicó", "Linares", "Constitución", "Parral"]},
    {"region": "Ñuble", "ciudades": ["Chillán", "San Carlos", "Bulnes", "Quirihue", "Yungay"]},
    {
        "region": "Biobío",
        "ciudades": ["Concepción", "Talcahuano", "Los Ángeles", "Coronel", "Chiguayante"],
    },
    {
        "region": "La Araucanía",
        "ciudades": ["Temuco", "Villarrica", "Angol", "Pucón", "Padre Las Casas"],
    },
    {
        "region": "Los Ríos",
        "ciudades": ["Valdivia", "La Unión", "Río Bueno", "Panguipulli", "Futrono"],
    },
    {
        "region": "Los Lagos",
        "ciudades": ["Puerto Montt", "Osorno", "Castro", "Ancud", "Puerto Varas"],
    },
    {"region": "Aysén", "ciudades": ["Coyhaique", "Puerto Aysén", "Chile Chico", "Cochrane"]},
    {
        "region": "Magallanes",
        "ciudades": ["Punta Arenas", "Puerto Natales", "Porvenir", "Puerto Williams"],
    },
]


def _find_chile_json():
    """Busca el JSON de regiones/ciudades Chile en data/ del proyecto o rutas habituales."""
    base = Path(settings.BASE_DIR)
    candidates = [
        base / "data" / "regiones_ciudades.json",
        base / "data" / "regiones_y_ciudades_chile.json",
        base / "data" / "root_data" / "regiones_ciudades.json",
        Path("data/regiones_ciudades.json"),
        Path("data/regiones_y_ciudades_chile.json"),
    ]
    for p in candidates:
        try:
            p = p.resolve()
            if p.is_file():
                return p
        except (OSError, RuntimeError):
            continue
    return None


def _iter_regiones_ciudades(datos):
    """Normaliza formato: list [{region, ciudades}] o dict {region: [ciudades]} -> (region, ciudades)."""
    if isinstance(datos, list):
        for item in datos:
            yield item["region"], item.get("ciudades", [])
    else:
        for nombre_region, ciudades in datos.items():
            yield nombre_region, ciudades if isinstance(ciudades, list) else []


class Command(BaseCommand):
    help = "Carga regiones y ciudades de Chile (TallerRegion/TallerCiudad) desde JSON o datos embebidos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=None,
            help="Ruta al JSON (opcional; si no existe usa datos embebidos)",
        )

    def handle(self, *args, **kwargs):
        path_arg = kwargs.get("path")
        datos = None
        if path_arg:
            json_path = Path(path_arg).resolve()
            if json_path.is_file():
                with open(json_path, encoding="utf-8") as f:
                    datos = json.load(f)
                self.stdout.write(f"Usando archivo: {json_path}")
        else:
            json_path = _find_chile_json()
            if json_path and json_path.is_file():
                with open(json_path, encoding="utf-8") as f:
                    datos = json.load(f)
                self.stdout.write(f"Usando archivo: {json_path}")

        if datos is None:
            self.stdout.write(
                self.style.WARNING("No se encontro JSON. Usando datos embebidos (16 regiones).")
            )
            datos = REGIONES_CHILE_EMBED

        nuevas_regiones = 0
        nuevas_ciudades = 0

        for nombre_region, ciudades in _iter_regiones_ciudades(datos):
            region, region_creada = TallerRegion.objects.get_or_create(nombre=nombre_region)
            if region_creada:
                nuevas_regiones += 1
            for ciudad in ciudades:
                _, ciudad_creada = TallerCiudad.objects.get_or_create(nombre=ciudad, region=region)
                if ciudad_creada:
                    nuevas_ciudades += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"OK: {nuevas_regiones} regiones y {nuevas_ciudades} ciudades cargadas."
            )
        )
