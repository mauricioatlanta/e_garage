# Generated manually - Carga regiones/ciudades de Chile cuando TallerRegion está vacío

import json
from pathlib import Path

from django.conf import settings
from django.db import migrations


def _find_chile_json():
    """Busca el JSON de regiones/ciudades Chile."""
    base = Path(settings.BASE_DIR)
    candidates = [
        base / "data" / "regiones_ciudades.json",
        base / "data" / "regiones_y_ciudades_chile.json",
        base / "taller" / "fixtures" / "regiones_y_ciudades_chile.json",
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
    """Normaliza formato: list [{region, ciudades}] o dict {region: [ciudades]}."""
    if isinstance(datos, list):
        for item in datos:
            yield item["region"], item.get("ciudades", [])
    else:
        for nombre_region, ciudades in datos.items():
            yield nombre_region, ciudades if isinstance(ciudades, list) else []


def load_regiones_chile(apps, schema_editor):
    """Carga regiones y ciudades de Chile si TallerRegion está vacío."""
    TallerRegion = apps.get_model("taller", "TallerRegion")
    TallerCiudad = apps.get_model("taller", "TallerCiudad")

    if TallerRegion.objects.exists():
        return  # Ya hay datos, no hacer nada

    json_path = _find_chile_json()
    if not json_path or not json_path.is_file():
        return  # Sin JSON, saltar (el comando manual cargará después)

    with open(json_path, encoding="utf-8") as f:
        datos = json.load(f)

    for nombre_region, ciudades in _iter_regiones_ciudades(datos):
        region, _ = TallerRegion.objects.get_or_create(nombre=nombre_region)
        for ciudad_nombre in ciudades:
            TallerCiudad.objects.get_or_create(nombre=ciudad_nombre, region=region)


def reverse_load(apps, schema_editor):
    """No revertir - los datos pueden estar en uso."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0090_pieza_desarme_company_label"),
    ]

    operations = [
        migrations.RunPython(load_regiones_chile, reverse_load),
    ]
