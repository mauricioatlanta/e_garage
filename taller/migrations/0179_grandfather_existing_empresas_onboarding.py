from django.db import migrations
from django.utils import timezone


def grandfather_existing_empresas(apps, schema_editor):
    Empresa = apps.get_model("taller", "Empresa")
    now = timezone.now()
    Empresa.objects.filter(onboarding_completado=False).update(
        onboarding_completado=True,
        onboarding_completed_at=now,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("taller", "0178_preciometal"),
    ]

    operations = [
        migrations.RunPython(grandfather_existing_empresas, migrations.RunPython.noop),
    ]
