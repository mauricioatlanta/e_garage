# Generated manually for eGarage Air - WhatsApp v2 Final

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taller', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmpresaWhatsAppConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number_id', models.CharField(help_text='ID del número de teléfono en Meta Cloud API', max_length=50)),
                ('allowed_operator_phone', models.CharField(help_text='Teléfono del operador autorizado (formato: 56912345678)', max_length=20)),
                ('is_enabled', models.BooleanField(default=True, help_text='Activar/desactivar integración WhatsApp')),
                ('enable_audio', models.BooleanField(default=True, help_text='Habilitar procesamiento de audios con IA')),
                ('enable_ocr', models.BooleanField(default=True, help_text='Habilitar reconocimiento de patentes por OCR')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('empresa', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_config', to='taller.empresa')),
            ],
            options={
                'verbose_name': 'Configuración WhatsApp Empresa',
                'verbose_name_plural': 'Configuraciones WhatsApp Empresas',
                'db_table': 'whatsapp_empresa_config',
            },
        ),
        migrations.CreateModel(
            name='WhatsAppSession',
            fields=[
                ('operator_phone', models.CharField(help_text='Teléfono del operador (formato: 56912345678)', max_length=20, primary_key=True, serialize=False)),
                ('estado', models.CharField(choices=[('IDLE', 'Inactivo'), ('WAITING_PLATE', 'Esperando Patente'), ('WAITING_MILEAGE', 'Esperando Kilometraje'), ('WAITING_ACTION', 'Esperando Acción'), ('WAITING_CONFIRM', 'Esperando Confirmación')], db_index=True, default='IDLE', max_length=50)),
                ('contexto', models.JSONField(default=dict, help_text='Contexto de la conversación: documento_id, vehiculo_id, cliente_id, etc.')),
                ('last_interaction', models.DateTimeField(auto_now=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_sessions', to='taller.empresa')),
            ],
            options={
                'verbose_name': 'Sesión WhatsApp',
                'verbose_name_plural': 'Sesiones WhatsApp',
                'db_table': 'whatsapp_sessions',
            },
        ),
        migrations.AddIndex(
            model_name='whatsappsession',
            index=models.Index(fields=['empresa', 'estado'], name='whatsapp_se_empresa__idx'),
        ),
        migrations.AddIndex(
            model_name='whatsappsession',
            index=models.Index(fields=['last_interaction'], name='whatsapp_se_last_in_idx'),
        ),
    ]
