from django.db import migrations

def generar_codigo_marca(apps, schema_editor):
    Marca = apps.get_model('taller', 'Marca')
    for marca in Marca.objects.all():
        if not marca.codigo:
            # Generar código a partir del nombre (primeras 3 letras en mayúscula)
            base_codigo = marca.nombre[:3].upper().strip()
            codigo = base_codigo
            counter = 1
            
            # Verificar y evitar duplicados
            while Marca.objects.filter(codigo=codigo).exclude(id=marca.id).exists():
                codigo = f"{base_codigo}{counter}"
                counter += 1
                
            marca.codigo = codigo
            marca.save()

class Migration(migrations.Migration):
    dependencies = [
        ('taller', '0001_initial'),
        ('taller', '0004_merge_20250902_2231'),  # Agregar dependencia del merge
    ]

    operations = [
        migrations.RunPython(generar_codigo_marca),
    ]
