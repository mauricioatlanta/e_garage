from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0109_snapshotqueueitem_locked_at_and_more"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="documento",
            constraint=models.UniqueConstraint(
                fields=("empresa", "tipo", "numero"),
                name="uniq_documento_empresa_tipo_numero",
            ),
        ),
    ]
