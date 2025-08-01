# Generated by Django 5.1.6 on 2025-07-23 00:46

import datetime
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taller', '0002_logauditoria'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoNotificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('evento', models.CharField(choices=[('DOCUMENTO_CREADO', 'Documento Creado'), ('SUSCRIPCION_VENCE', 'Suscripción por Vencer'), ('SUSCRIPCION_VENCIDA', 'Suscripción Vencida'), ('MANTENIMIENTO_RECORDATORIO', 'Recordatorio de Mantenimiento'), ('REVISION_VEHICULO', 'Revisión de Vehículo'), ('PAGO_PENDIENTE', 'Pago Pendiente'), ('CLIENTE_INACTIVO', 'Cliente Inactivo'), ('BACKUP_COMPLETADO', 'Backup Completado'), ('ERROR_SISTEMA', 'Error del Sistema')], max_length=50)),
                ('tipo', models.CharField(choices=[('EMAIL', 'Email'), ('SMS', 'SMS'), ('WHATSAPP', 'WhatsApp'), ('PUSH', 'Push Notification'), ('SISTEMA', 'Notificación del Sistema')], max_length=20)),
                ('activo', models.BooleanField(default=True)),
                ('template_asunto', models.CharField(max_length=200)),
                ('template_mensaje', models.TextField()),
                ('dias_anticipacion', models.PositiveIntegerField(default=0, help_text='Días de anticipación para el recordatorio')),
            ],
            options={
                'verbose_name': 'Tipo de Notificación',
                'verbose_name_plural': 'Tipos de Notificaciones',
            },
        ),
        migrations.CreateModel(
            name='ConfiguracionNotificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_activo', models.BooleanField(default=True)),
                ('email_smtp_host', models.CharField(default='smtp.gmail.com', max_length=100)),
                ('email_smtp_port', models.PositiveIntegerField(default=587)),
                ('email_use_tls', models.BooleanField(default=True)),
                ('email_usuario', models.EmailField(blank=True, max_length=254)),
                ('email_password', models.CharField(blank=True, help_text='Password de aplicación', max_length=100)),
                ('email_remitente', models.EmailField(blank=True, max_length=254)),
                ('whatsapp_activo', models.BooleanField(default=False)),
                ('whatsapp_api_token', models.CharField(blank=True, max_length=200)),
                ('whatsapp_numero_business', models.CharField(blank=True, max_length=20)),
                ('sms_activo', models.BooleanField(default=False)),
                ('sms_api_token', models.CharField(blank=True, max_length=200)),
                ('sms_proveedor', models.CharField(choices=[('twilio', 'Twilio'), ('nexmo', 'Nexmo'), ('local', 'Proveedor Local')], default='twilio', max_length=50)),
                ('notificar_documentos', models.BooleanField(default=True)),
                ('notificar_suscripcion', models.BooleanField(default=True)),
                ('notificar_mantenimiento', models.BooleanField(default=True)),
                ('dias_recordatorio_suscripcion', models.PositiveIntegerField(default=7)),
                ('dias_recordatorio_mantenimiento', models.PositiveIntegerField(default=30)),
                ('hora_inicio_envio', models.TimeField(default=datetime.time(8, 0))),
                ('hora_fin_envio', models.TimeField(default=datetime.time(20, 0))),
                ('enviar_fines_semana', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('empresa', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='config_notificaciones', to='taller.empresa')),
            ],
            options={
                'verbose_name': 'Configuración de Notificaciones',
                'verbose_name_plural': 'Configuraciones de Notificaciones',
            },
        ),
        migrations.CreateModel(
            name='RecordatorioMantenimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_mantenimiento', models.CharField(choices=[('ACEITE', 'Cambio de Aceite'), ('FRENOS', 'Revisión de Frenos'), ('NEUMATICOS', 'Rotación de Neumáticos'), ('REVISION_GENERAL', 'Revisión General'), ('ALINEACION', 'Alineación y Balanceo'), ('BATERIA', 'Revisión de Batería'), ('FILTROS', 'Cambio de Filtros'), ('BUJIAS', 'Cambio de Bujías'), ('CORREA_DISTRIBUCION', 'Correa de Distribución'), ('PERSONALIZADO', 'Mantenimiento Personalizado')], max_length=30)),
                ('descripcion', models.TextField()),
                ('fecha_programada', models.DateField()),
                ('kilometraje_programado', models.PositiveIntegerField(blank=True, null=True)),
                ('dias_recordatorio', models.PositiveIntegerField(default=7)),
                ('estado', models.CharField(choices=[('PROGRAMADO', 'Programado'), ('NOTIFICADO', 'Notificado'), ('REALIZADO', 'Realizado'), ('CANCELADO', 'Cancelado'), ('VENCIDO', 'Vencido')], default='PROGRAMADO', max_length=20)),
                ('fecha_realizado', models.DateField(blank=True, null=True)),
                ('notas_realizacion', models.TextField(blank=True)),
                ('notificacion_enviada', models.BooleanField(default=False)),
                ('fecha_notificacion', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taller.cliente')),
                ('documento_origen', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='taller.documento')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taller.empresa')),
                ('vehiculo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taller.vehiculo')),
            ],
            options={
                'verbose_name': 'Recordatorio de Mantenimiento',
                'verbose_name_plural': 'Recordatorios de Mantenimiento',
                'ordering': ['fecha_programada'],
            },
        ),
        migrations.CreateModel(
            name='NotificacionEnviada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destinatario_email', models.EmailField(blank=True, max_length=254)),
                ('destinatario_telefono', models.CharField(blank=True, max_length=20)),
                ('destinatario_nombre', models.CharField(max_length=100)),
                ('asunto', models.CharField(max_length=200)),
                ('mensaje', models.TextField()),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('ENVIADO', 'Enviado'), ('ENTREGADO', 'Entregado'), ('ERROR', 'Error'), ('REINTENTO', 'Reintento')], default='PENDIENTE', max_length=20)),
                ('intentos', models.PositiveIntegerField(default=0)),
                ('fecha_programada', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_enviado', models.DateTimeField(blank=True, null=True)),
                ('fecha_entregado', models.DateTimeField(blank=True, null=True)),
                ('error_mensaje', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='taller.cliente')),
                ('documento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='taller.documento')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taller.empresa')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('tipo_notificacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taller.tiponotificacion')),
            ],
            options={
                'verbose_name': 'Notificación Enviada',
                'verbose_name_plural': 'Notificaciones Enviadas',
                'ordering': ['-created_at'],
            },
        ),
    ]
