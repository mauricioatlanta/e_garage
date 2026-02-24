# Generated manually for removing TallerInfo model
# This migration removes the TallerInfo model after data has been migrated to Empresa
from django.db import migrations


def migrate_tallerinfo_to_empresa(apps, schema_editor):
    """
    Migra cualquier dato restante de TallerInfo a Empresa.
    Esta función es segura y NO elimina datos de Vehiculo o Cliente.
    """
    TallerInfo = apps.get_model("taller", "TallerInfo")
    Empresa = apps.get_model("taller", "Empresa")

    # Contar registros de TallerInfo
    count = TallerInfo.objects.count()
    if count == 0:
        print("No hay registros de TallerInfo para migrar")
        return

    print(f"Migrando {count} registros de TallerInfo a Empresa...")
    migrated = 0
    skipped = 0

    for taller_info in TallerInfo.objects.all():
        try:
            # Buscar la empresa asociada al usuario
            empresa = Empresa.objects.get(user=taller_info.user)

            # Actualizar campos de Empresa con datos de TallerInfo si están vacíos
            updated = False
            if not empresa.nombre_taller or empresa.nombre_taller == "Mi Taller":
                if taller_info.nombre_taller:
                    empresa.nombre_taller = taller_info.nombre_taller
                    updated = True

            if not empresa.telefono and taller_info.telefono:
                empresa.telefono = taller_info.telefono
                updated = True

            if not empresa.ha_usado_prueba and taller_info.ha_usado_prueba:
                empresa.ha_usado_prueba = True
                updated = True

            if updated:
                empresa.save(update_fields=["nombre_taller", "telefono", "ha_usado_prueba"])
                migrated += 1
                print(f"  Migrado TallerInfo para usuario {taller_info.user.email}")
            else:
                skipped += 1
                print(f"  Saltado (datos ya presentes) para usuario {taller_info.user.email}")

        except Empresa.DoesNotExist:
            # Si no existe Empresa, crear una nueva con los datos de TallerInfo
            empresa = Empresa.objects.create(
                user=taller_info.user,
                nombre_taller=taller_info.nombre_taller or "Mi Taller",
                telefono=taller_info.telefono or "",
                ha_usado_prueba=taller_info.ha_usado_prueba,
            )
            migrated += 1
            print(f"  Creada Empresa desde TallerInfo para usuario {taller_info.user.email}")

    print(f"Migracion completada: {migrated} migrados, {skipped} saltados")


def reverse_migration(apps, schema_editor):
    """
    Función de reversión (no crea TallerInfo de nuevo, solo documenta)
    """
    print("Reversion: El modelo TallerInfo no se recreara automaticamente")


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0048_clientecredencial_clientetoken"),
    ]

    operations = [
        # Primero migrar datos de TallerInfo a Empresa
        migrations.RunPython(migrate_tallerinfo_to_empresa, reverse_migration),
        # Luego eliminar el modelo TallerInfo
        migrations.DeleteModel(
            name="TallerInfo",
        ),
    ]
