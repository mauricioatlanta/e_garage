# Generated by Django 5.2.3 on 2025-07-09 14:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taller', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mecanico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='documento',
            name='mecanico',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='taller.mecanico'),
        ),
    ]
