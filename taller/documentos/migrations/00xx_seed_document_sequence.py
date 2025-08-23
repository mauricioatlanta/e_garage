from django.db import migrations

def seed_document_sequence(apps, schema_editor):
    Documento = apps.get_model('documentos', 'Documento')
    DocumentSequence = apps.get_model('documentos', 'DocumentSequence')
    from django.db.models import Max

    qs = (Documento.objects
          .filter(numero__isnull=False)
          .values('empresa_id', 'tipo')
          .annotate(mx=Max('numero')))

    for row in qs.iterator():
        seq, _ = DocumentSequence.objects.get_or_create(
            empresa_id=row['empresa_id'],
            tipo=row['tipo'],
            defaults={'next_number': (row['mx'] or 0) + 1}
        )
        target = (row['mx'] or 0) + 1
        if seq.next_number < target:
            seq.next_number = target
            seq.save(update_fields=['next_number'])

class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ('documentos', '00xx_create_documentsequence'),
    ]
    operations = [
        migrations.RunPython(seed_document_sequence, migrations.RunPython.noop),
    ]
