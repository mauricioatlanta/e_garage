from django.db import migrations

# Semilla del catálogo de servicios sugeridos por rubro.
# `pais=None` = fallback internacional (DEFAULT); las entradas específicas por
# país se agregan posteriormente. La mano de obra NO lleva precio predefinido.
SEED = [
    # (rubro, nombre_es, nombre_en, orden)
    ("WORKSHOP", "Cambio de aceite y filtro", "Oil & filter change", 10),
    ("WORKSHOP", "Frenos (pastillas y discos)", "Brakes (pads & rotors)", 20),
    ("WORKSHOP", "Diagnóstico computarizado (escáner)", "Computerized diagnosis (scanner)", 30),
    ("WORKSHOP", "Afinamiento / Sincronización", "Tune-up", 40),
    ("WORKSHOP", "Suspensión y dirección", "Suspension & steering", 50),
    ("WORKSHOP", "Sistema de escape", "Exhaust system", 60),
    ("WORKSHOP", "Embrague", "Clutch", 70),
    ("WORKSHOP", "Correa de distribución", "Timing belt", 80),
    ("WORKSHOP", "Batería y sistema de carga", "Battery & charging system", 90),
    ("WORKSHOP", "Refrigeración / Radiador", "Cooling system / radiator", 100),
    ("BODYSHOP", "Reparación de chapa (hojalatería)", "Body repair", 10),
    ("BODYSHOP", "Pintura / Repintado", "Paint / repaint", 20),
    ("BODYSHOP", "Enderezado de bastidor", "Frame straightening", 30),
    ("BODYSHOP", "Desabolladura sin pintura (PDR)", "Paintless dent repair (PDR)", 40),
    ("GLASS", "Reemplazo de parabrisas", "Windshield replacement", 10),
    ("GLASS", "Reparación de vidrios laterales", "Side glass repair", 20),
    ("GLASS", "Instalación de luneta", "Rear window installation", 30),
    ("ELECTRIC", "Diagnóstico eléctrico", "Electrical diagnosis", 10),
    ("ELECTRIC", "Alternador / Arranque", "Alternator / starter", 20),
    ("ELECTRIC", "Instalación de audio", "Audio installation", 30),
    ("ELECTRIC", "Sensores / Centralita", "Sensors / ECU", 40),
    ("TIRE", "Montaje y balanceo", "Mount & balance", 10),
    ("TIRE", "Alineación", "Wheel alignment", 20),
    ("TIRE", "Reparación de pinchazo", "Flat repair", 30),
    ("DETAILING", "Lavado exterior / interior", "Exterior / interior wash", 10),
    ("DETAILING", "Pulido y encerado", "Polish & wax", 20),
    ("DETAILING", "Limpieza de tapicería", "Upholstery cleaning", 30),
    ("FLEET", "Mantenimiento preventivo de flota", "Fleet preventive maintenance", 10),
    ("FLEET", "Inspección pre-operacional", "Pre-operational inspection", 20),
]


def forwards(apps, schema_editor):
    CatalogoServicio = apps.get_model("taller", "CatalogoServicio")
    for rubro, nombre, nombre_en, orden in SEED:
        CatalogoServicio.objects.get_or_create(
            rubro=rubro,
            pais=None,
            nombre=nombre,
            defaults={"nombre_en": nombre_en, "orden": orden, "activo": True},
        )


def backwards(apps, schema_editor):
    CatalogoServicio = apps.get_model("taller", "CatalogoServicio")
    for rubro, nombre, _nombre_en, _orden in SEED:
        CatalogoServicio.objects.filter(rubro=rubro, pais=None, nombre=nombre).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0201_alter_lineaservicio_precio_unitario_catalogoservicio_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
