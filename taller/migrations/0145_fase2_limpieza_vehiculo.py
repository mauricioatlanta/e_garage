from django.db import migrations


class Migration(migrations.Migration):
    """
    MIGRACIÓN DIFERIDA — no aplicar en la misma ventana que 0142-0144.

    Elimina la columna 'vehiculo' (FK a taller_vehiculo) de las 5 tablas.
    Cada RemoveField dropa en Postgres: la columna vehiculo_id, el FK constraint
    automático de Django, y el índice de FK automático.

    Condiciones antes de aplicar (todas deben cumplirse):
    1. Los 17 archivos de código de la lista están actualizados y desplegados.
    2. Mínimo 14 días en producción sin referencias a vehiculo/vehiculo_id en
       logs de error provenientes de estas 5 tablas.
    3. grep -r confirma 0 referencias a vehiculo_id en código activo de las 5 tablas.
    4. Aprobación explícita antes de correr manage.py migrate en producción.
    """

    dependencies = [
        ("taller", "0144_fase2_schema_vehiculo_desarme"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="piezadesarme",
            name="vehiculo",
        ),
        migrations.RemoveField(
            model_name="sugerenciapiezadesarme",
            name="vehiculo",
        ),
        migrations.RemoveField(
            model_name="preciohistoricopieza",
            name="vehiculo",
        ),
        migrations.RemoveField(
            model_name="vehiculofinancialsnapshot",
            name="vehiculo",
        ),
        migrations.RemoveField(
            model_name="vehiclefinancialevent",
            name="vehiculo",
        ),
    ]
