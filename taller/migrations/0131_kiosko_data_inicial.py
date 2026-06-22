from datetime import datetime

from django.db import migrations

MARCAS_CL = [
    "Chevrolet",
    "Hyundai",
    "Toyota",
    "Nissan",
    "Kia",
    "Suzuki",
    "Ford",
    "Mazda",
    "Volkswagen",
    "Mitsubishi",
]

# (marca, modelo, anio_inicio, anio_fin o None)
MODELOS_CL = [
    ("Chevrolet", "Sail", 2010, None),
    ("Chevrolet", "Spark", 2005, None),
    ("Chevrolet", "Cruze", 2011, None),
    ("Hyundai", "Accent", 2000, None),
    ("Hyundai", "Tucson", 2004, None),
    ("Hyundai", "Elantra", 2000, None),
    ("Toyota", "Corolla", 1995, None),
    ("Toyota", "Hilux", 2005, None),
    ("Toyota", "RAV4", 2005, None),
    ("Nissan", "Tiida", 2006, 2020),
    ("Nissan", "Frontier", 2005, None),
    ("Nissan", "Sentra", 2000, None),
    ("Kia", "Rio", 2005, None),
    ("Kia", "Sportage", 2010, None),
    ("Suzuki", "Swift", 2005, None),
    ("Suzuki", "Grand Vitara", 2006, 2019),
    ("Ford", "Focus", 2005, 2019),
    ("Ford", "Ranger", 2000, None),
    ("Mazda", "3", 2005, None),
    ("Mazda", "CX-5", 2012, None),
    ("Volkswagen", "Polo", 2010, None),
    ("Volkswagen", "Gol", 2005, 2018),
    ("Mitsubishi", "L200", 2005, None),
    ("Mitsubishi", "ASX", 2011, None),
]

ALIASES = [
    # (pieza_canonica, termino_busqueda, pais)
    ("alternador", "alternador", ""),
    ("alternador", "generador", "MX"),
    ("radiador", "radiador", ""),
    ("transmision", "caja de cambios", "CL"),
    ("transmision", "transmision", ""),
    ("parachoque", "bumper", ""),
    ("parachoque", "paragolpe", "AR"),
    ("amortiguador", "shock", ""),
    ("amortiguador", "amortiguador", ""),
]


def poblar_marcas_y_aliases(apps, schema_editor):
    MarcaVehiculo = apps.get_model("taller", "MarcaVehiculo")
    ModeloVehiculo = apps.get_model("taller", "ModeloVehiculo")
    AliasRepuesto = apps.get_model("taller", "AliasRepuesto")

    anio_actual = datetime.now().year

    marca_objs = {}
    for nombre in MARCAS_CL:
        marca, _ = MarcaVehiculo.objects.get_or_create(
            nombre=nombre,
            defaults={"pais_origen": "Varios", "activa": True, "anio_inicio": 1990},
        )
        marca_objs[nombre] = marca

    for nombre_marca, nombre_modelo, anio_ini, anio_fin in MODELOS_CL:
        marca = marca_objs.get(nombre_marca)
        if not marca:
            continue
        ModeloVehiculo.objects.update_or_create(
            marca=marca,
            nombre=nombre_modelo,
            defaults={
                "anio_inicio": anio_ini,
                "anio_fin": anio_fin,
                "activo": True,
                "paises": "CL",
            },
        )

    for canonica, termino, pais in ALIASES:
        AliasRepuesto.objects.get_or_create(
            pieza_canonica=canonica,
            termino_busqueda=termino,
            pais=pais,
        )


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0130_kiosko_fase1_y_fase2"),
    ]

    operations = [
        migrations.RunPython(poblar_marcas_y_aliases, revertir),
    ]
