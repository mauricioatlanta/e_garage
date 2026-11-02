from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


def mark_existing_profiles_as_not_forced(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    PerfilUsuario = apps.get_model("taller", "PerfilUsuario")
    existing_profile_user_ids = set(PerfilUsuario.objects.values_list("user_id", flat=True))
    missing_profiles = [
        PerfilUsuario(user_id=user_id, must_change_password=False)
        for user_id in User.objects.exclude(id__in=existing_profile_user_ids).values_list("id", flat=True)
    ]
    PerfilUsuario.objects.bulk_create(missing_profiles, ignore_conflicts=True)
    PerfilUsuario.objects.update(must_change_password=False)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("taller", "0190_partapplication"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="must_change_password",
            field=models.BooleanField(default=True, verbose_name="Debe cambiar contraseña"),
        ),
        migrations.RunPython(mark_existing_profiles_as_not_forced, migrations.RunPython.noop),
        migrations.AddField(
            model_name="publicpageview",
            name="host",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name="publicanalyticssession",
            name="host",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.CreateModel(
            name="AbandonedLead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(blank=True, max_length=160)),
                ("whatsapp", models.CharField(blank=True, db_index=True, max_length=32)),
                ("email", models.EmailField(blank=True, db_index=True, max_length=254)),
                ("rubro", models.CharField(blank=True, db_index=True, max_length=80)),
                ("pais", models.CharField(blank=True, db_index=True, max_length=8)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("contactado", models.BooleanField(db_index=True, default=False)),
            ],
            options={
                "verbose_name": "Lead abandonado",
                "verbose_name_plural": "Leads abandonados",
                "ordering": ["-fecha_creacion"],
            },
        ),
        migrations.AddIndex(
            model_name="abandonedlead",
            index=models.Index(fields=["contactado", "fecha_creacion"], name="taller_aban_contact_0f44d7_idx"),
        ),
        migrations.AddIndex(
            model_name="abandonedlead",
            index=models.Index(fields=["pais", "rubro", "fecha_creacion"], name="taller_aban_pais_1ba6ee_idx"),
        ),
    ]
