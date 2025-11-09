# Generated manually for data normalization
from django.db import migrations


def normalize_empresa_data(apps, schema_editor):
    """Normaliza datos de empresa según las nuevas reglas de negocio"""
    Empresa = apps.get_model("taller", "Empresa")

    US_TZS = {
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Anchorage",
        "Pacific/Honolulu",
        "America/Phoenix",
    }
    CL_TZS = {"America/Santiago"}

    print("🔄 Normalizando datos de empresa...")
    empresas_procesadas = 0
    empresas_modificadas = 0

    for e in Empresa.objects.all().iterator():
        empresas_procesadas += 1
        changed = False

        # Moneda por país
        if e.pais == "US" and e.moneda != "USD":
            e.moneda = "USD"
            changed = True
            print(f"  📝 Empresa {e.id}: Moneda cambiada a USD (era {e.moneda})")
        elif e.pais == "CL" and e.moneda != "CLP":
            e.moneda = "CLP"
            changed = True
            print(f"  📝 Empresa {e.id}: Moneda cambiada a CLP (era {e.moneda})")

        # TZ válida por país (si no lo es, poner default seguro)
        tz = (e.zona_horaria or "").strip()
        if e.pais == "US":
            if tz not in US_TZS:
                old_tz = e.zona_horaria
                e.zona_horaria = "America/New_York"
                changed = True
                print(
                    f"  🌍 Empresa {e.id}: TZ cambiada a America/New_York (era {old_tz})"
                )
        else:  # CL
            if tz not in CL_TZS:
                old_tz = e.zona_horaria
                e.zona_horaria = "America/Santiago"
                changed = True
                print(
                    f"  🌍 Empresa {e.id}: TZ cambiada a America/Santiago (era {old_tz})"
                )

        if changed:
            e.save(update_fields=["moneda", "zona_horaria"])
            empresas_modificadas += 1

    print("✅ Normalización completada:")
    print(f"   📊 Empresas procesadas: {empresas_procesadas}")
    print(f"   🔧 Empresas modificadas: {empresas_modificadas}")


def noop_reverse(apps, schema_editor):
    """No revertimos datos normalizados - es una operación de limpieza"""
    print("ℹ️  No se revierten datos normalizados (operación de limpieza)")


class Migration(migrations.Migration):
    dependencies = [
        ("taller", "0011_improve_empresa_model_robust"),
    ]

    operations = [
        migrations.RunPython(normalize_empresa_data, noop_reverse),
    ]
