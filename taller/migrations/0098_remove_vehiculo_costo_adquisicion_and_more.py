from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taller', '0097_safe_add_precio_compra'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vehiculo',
            name='costo_adquisicion',
        ),
    ]
