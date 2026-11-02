from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taller", "0172_merge_analytics_notificaciones"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publicpageview",
            name="page_type",
            field=models.CharField(
                choices=[
                    ("home", "Página principal"),
                    ("welcome", "Bienvenida"),
                    ("landing", "Landing"),
                ],
                db_index=True,
                max_length=20,
            ),
        ),
    ]
