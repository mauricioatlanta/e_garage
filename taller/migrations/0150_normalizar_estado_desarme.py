# Normaliza taller_vehiculo.estado_desarme (tipo_uso=DESARME) y
# taller_vehiculodesarme.estado_desarme a los choices válidos de
# VehiculoDesarme.ESTADO_DESARME_CHOICES (INGRESADO/DESARMANDO/DESARMADO/
# AGOTADO/RECUPERADO/CERRADO/BAJA).
#
# Motivo: hasta ahora taller/desarme/forms.py usaba su propia lista de
# choices (en_yarda/en_proceso/completado/vendido/baja), distinta de la del
# modelo. Django no valida `choices=` a nivel de base de datos (sin CHECK
# constraint), así que esos valores quedaron persistidos sin error. Antes de
# cortar VehiculoDesarmeForm a VehiculoDesarme (Fase 6.2), tienen que
# normalizarse o el modelo los va a rechazar en cuanto pase por full_clean().
#
# Mapeo (confirmado por Mauricio, no inferido):
#   EN_DESARME -> DESARMANDO
#   en_yarda   -> INGRESADO
#   ACTIVO     -> DESARMANDO
#   en_proceso -> DESARMANDO
#
# Cualquier valor no vacío que no esté ni en este mapeo ni ya sea un choice
# válido del modelo se deja SIN TOCAR y se loguea aparte (ver
# "SIN TOCAR" en el log) para decidir manualmente qué hacer con él.
# Valores vacíos ('') y NULL se dejan como están.

import logging

from django.db import migrations
from django.db.models import Count

logger = logging.getLogger(__name__)

MAPEO_FORWARD = {
    "EN_DESARME": "DESARMANDO",
    "en_yarda": "INGRESADO",
    "ACTIVO": "DESARMANDO",
    "en_proceso": "DESARMANDO",
}

# Reverso best-effort: EN_DESARME, ACTIVO y en_proceso colapsan todos a
# DESARMANDO hacia adelante, así que el reverso NO puede reconstruir cuál
# era el valor original de cada fila individual -- no es lossless. Se
# revierte a "en_proceso" como representante único de DESARMANDO (es el
# valor que producía el form en vivo antes de este cambio) y "en_yarda"
# para INGRESADO. Filas que originalmente eran EN_DESARME o ACTIVO quedan
# como "en_proceso" tras revertir, no con su valor exacto original.
MAPEO_BACKWARD = {
    "DESARMANDO": "en_proceso",
    "INGRESADO": "en_yarda",
}

# Duplicado deliberadamente (no se importa el modelo real): una migración de
# datos no debe depender de que taller.models.vehiculo_desarme no cambie
# después de que esta migración ya se aplicó.
CHOICES_VALIDAS_MODELO = {
    "INGRESADO",
    "DESARMANDO",
    "DESARMADO",
    "AGOTADO",
    "RECUPERADO",
    "CERRADO",
    "BAJA",
}


def _distribucion(qs_base):
    return list(
        qs_base.exclude(estado_desarme__isnull=True)
        .exclude(estado_desarme="")
        .values("estado_desarme")
        .annotate(n=Count("id"))
        .order_by("-n")
    )


def _normalizar(apps, mapeo, direccion):
    Vehiculo = apps.get_model("taller", "Vehiculo")
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")

    tablas = [
        ("Vehiculo(tipo_uso=DESARME)", Vehiculo.objects.filter(tipo_uso="DESARME")),
        ("VehiculoDesarme", VehiculoDesarme.objects.all()),
    ]

    for nombre, qs_base in tablas:
        logger.info("0150 [%s] %s: distribucion ANTES: %s", direccion, nombre, _distribucion(qs_base))

        total_actualizadas = 0
        for valor_viejo, valor_nuevo in mapeo.items():
            n = qs_base.filter(estado_desarme=valor_viejo).update(estado_desarme=valor_nuevo)
            if n:
                logger.info(
                    "0150 [%s] %s: %s -> %s (%s filas)",
                    direccion, nombre, valor_viejo, valor_nuevo, n,
                )
            total_actualizadas += n

        despues = _distribucion(qs_base)
        logger.info(
            "0150 [%s] %s: distribucion DESPUES (total actualizadas=%s): %s",
            direccion, nombre, total_actualizadas, despues,
        )

        no_reconocidos = sorted(
            {
                row["estado_desarme"]
                for row in despues
                if row["estado_desarme"] not in CHOICES_VALIDAS_MODELO
            }
        )
        if no_reconocidos:
            logger.warning(
                "0150 [%s] %s: SIN TOCAR -- valores fuera de "
                "VehiculoDesarme.ESTADO_DESARME_CHOICES y sin mapeo conocido: %s. "
                "Revisar manualmente antes de cortar el form a VehiculoDesarme.",
                direccion, nombre, no_reconocidos,
            )


def forwards(apps, schema_editor):
    _normalizar(apps, MAPEO_FORWARD, "forward")


def backwards(apps, schema_editor):
    _normalizar(apps, MAPEO_BACKWARD, "backward")


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0149_backfill_empresa_slugs"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
