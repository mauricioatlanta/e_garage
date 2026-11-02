from django.db import migrations

# Consolidación de la taxonomía de rubros.
# Origen: valores antiguos del catálogo (choices divergentes en 3 archivos).
# Destino: 14 códigos canónicos definidos en taller/config/rubros.py.
RUBRO_MIGRATION = {
    # ── Sin cambio (ya canónicos) ──
    "WORKSHOP": "WORKSHOP",
    "WORKSHOP_MOTO": "WORKSHOP_MOTO",
    "WORKSHOP_HEAVY": "WORKSHOP_HEAVY",
    "BODYSHOP": "BODYSHOP",
    "ELECTRIC": "ELECTRIC",
    "FLEET": "FLEET",
    "DESARMADURIA": "DESARMADURIA",
    "PARTS": "PARTS",
    "TIRE": "TIRE",
    "DETAILING": "DETAILING",
    "RECYCLING": "RECYCLING",
    "TOWING": "TOWING",
    "MIXED": "MIXED",
    # ── Consolidaciones (giro menor → giro canónico) ──
    "EXHAUST": "WORKSHOP",              # escapes/mufflers → mecánica
    "SUSPENSION_STEERING": "WORKSHOP",  # suspensión/dirección → mecánica
    "BRAKES": "WORKSHOP",               # frenos → mecánica
    "OBD_DIAGNOSTIC": "ELECTRIC",       # diagnóstico OBD-II → electrónica
    "AUDIO_ENTERTAINMENT": "ELECTRIC",  # audio → electrónica
    "CLASSIC_CARS": "WORKSHOP",         # restauración clásicos → mecánica
    "GAS_CONVERSION": "WORKSHOP",       # conversión a gas → mecánica
    "TUNING": "BODYSHOP",               # tuning/personalización → carrocería
    "FLEET_REPAIR": "FLEET",            # flotas corporativas → flotas
    "GLASS_AUDIO": "GLASS",             # vidrios+audio → vidrios (audio → ELECTRIC)
    "BODY_GLASS": "BODYSHOP",           # carrocería+vidrios → carrocería
}


def _map(value):
    """Mapea un valor antiguo a canónico; desconocido → se conserva (defensivo)."""
    if value is None:
        return value
    return RUBRO_MIGRATION.get(value, value)


def _normalize(rubros, principal=None):
    """Mapea, deduplica y asegura que `principal` quede primero (invariante)."""
    seen = []
    for value in (rubros or []):
        mapped = _map(value)
        if mapped and mapped not in seen:
            seen.append(mapped)
    if principal and principal not in seen:
        seen.insert(0, principal)
    return seen


def forwards(apps, schema_editor):
    ConfiguracionEmpresa = apps.get_model("taller", "ConfiguracionEmpresa")
    Servicio = apps.get_model("taller", "Servicio")
    ServicioBase = apps.get_model("taller", "ServicioBase")

    for config in ConfiguracionEmpresa.objects.all():
        new_principal = _map(config.rubro_principal)
        new_rubros = _normalize(config.rubros, new_principal)
        if new_principal != config.rubro_principal or new_rubros != (config.rubros or []):
            config.rubro_principal = new_principal
            config.rubros = new_rubros
            config.save(update_fields=["rubro_principal", "rubros"])

    for servicio in Servicio.objects.exclude(rubro_sugerido__isnull=True):
        nuevo = _map(servicio.rubro_sugerido)
        if nuevo != servicio.rubro_sugerido:
            servicio.rubro_sugerido = nuevo
            servicio.save(update_fields=["rubro_sugerido"])

    for servicio in Servicio.objects.exclude(rubro_efectivo__isnull=True):
        nuevo = _map(servicio.rubro_efectivo)
        if nuevo != servicio.rubro_efectivo:
            servicio.rubro_efectivo = nuevo
            servicio.save(update_fields=["rubro_efectivo"])

    for base in ServicioBase.objects.exclude(rubro_sugerido__isnull=True):
        nuevo = _map(base.rubro_sugerido)
        if nuevo != base.rubro_sugerido:
            base.rubro_sugerido = nuevo
            base.save(update_fields=["rubro_sugerido"])

    for base in ServicioBase.objects.all():
        nuevo = _normalize(base.rubros)
        if nuevo != (base.rubros or []):
            base.rubros = nuevo
            base.save(update_fields=["rubros"])


def backwards(apps, schema_editor):
    # La consolidación pierde granularidad (varios códigos viejos → uno canónico),
    # por lo que no es reversible byte a byte. Revertir requiere restaurar el
    # backup pre-migración. No-op explícito para que `migrate taller 0198` sea
    # seguro sin aplicar transformaciones espurias.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0198_alter_towingevidence_file"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
