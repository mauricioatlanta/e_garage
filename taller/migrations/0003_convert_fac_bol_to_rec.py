from django.db import migrations


def fac_bol_to_rec(apps, schema_editor):
    """
    Convierte documentos FAC (Factura) y BOL (Boleta) a REC (Recibo/Boleta)
    para mantener compatibilidad con datos existentes.
    """
    Documento = apps.get_model("taller", "Documento")

    # Convertir FAC → REC
    fac_count = Documento.objects.filter(tipo="FAC").count()
    if fac_count > 0:
        Documento.objects.filter(tipo="FAC").update(tipo="REC")
        print(f"✅ Convertidos {fac_count} documentos FAC → REC")

    # Convertir BOL → REC
    bol_count = Documento.objects.filter(tipo="BOL").count()
    if bol_count > 0:
        Documento.objects.filter(tipo="BOL").update(tipo="REC")
        print(f"✅ Convertidos {bol_count} documentos BOL → REC")

    if fac_count == 0 and bol_count == 0:
        print("ℹ️ No se encontraron documentos FAC o BOL para convertir")


def reverse_fac_bol_to_rec(apps, schema_editor):
    """
    Función de reversión (no se puede hacer automáticamente
    porque no sabemos cuáles eran FAC y cuáles BOL)
    """
    print("⚠️ No se puede revertir automáticamente la conversión FAC/BOL → REC")


class Migration(migrations.Migration):
    dependencies = [
        ("taller", "0002_alter_documento_tipo"),
    ]

    operations = [
        migrations.RunPython(fac_bol_to_rec, reverse_fac_bol_to_rec),
    ]
