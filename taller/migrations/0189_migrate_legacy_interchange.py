from django.db import migrations

def forwards_func(apps, schema_editor):
    InterchangePieza = apps.get_model("taller", "InterchangePieza")
    try:
        PartApplication = apps.get_model("taller", "PartApplication")
    except LookupError:
        return
    
    for item in InterchangePieza.objects.all():
        PartApplication.objects.get_or_create(
            codigo_pieza=item.codigo_pieza,
            marca=item.marca_compatible,
            modelo=item.modelo_compatible,
            defaults={
                'anio_desde': getattr(item, 'anio_desde', None),
                'anio_hasta': getattr(item, 'anio_hasta', None),
                'fuente': 'legacy_manual',
                'nivel_confianza': getattr(item, 'veces_confirmado', 5),
                'activo': True
            }
        )

def reverse_func(apps, schema_editor):
    try:
        PartApplication = apps.get_model("taller", "PartApplication")
    except LookupError:
        return
    PartApplication.objects.filter(fuente='legacy_manual').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('taller', '0188_repuesto_tire_pos_fields'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
