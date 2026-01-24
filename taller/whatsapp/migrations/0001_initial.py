# Generated migration for WhatsApp admin notifications
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taller', '0001_initial'),  # Ajustar según tu última migración
    ]

    operations = [
        migrations.CreateModel(
            name='WhatsAppAdminNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('nueva_suscripcion', 'Nueva Suscripción'), ('renovacion', 'Renovación'), ('cambio_plan', 'Cambio de Plan')], max_length=50)),
                ('plan', models.CharField(max_length=20)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('provider', models.CharField(default='dummy', max_length=20)),
                ('success', models.BooleanField(default=False)),
                ('message_id', models.CharField(blank=True, max_length=255, null=True)),
                ('error', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('comprobante_pago', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_notifications', to='taller.comprobantepago')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_admin_notifications', to='taller.empresa')),
                ('pago_pendiente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_notifications', to='taller.pagopendiente')),
            ],
            options={
                'verbose_name': 'Notificación WhatsApp Admin',
                'verbose_name_plural': 'Notificaciones WhatsApp Admin',
            },
        ),
        migrations.AlterUniqueTogether(
            name='whatsappadminnotification',
            unique_together={('comprobante_pago', 'event_type'), ('pago_pendiente', 'event_type')},
        ),
        migrations.AddIndex(
            model_name='whatsappadminnotification',
            index=models.Index(fields=['empresa', 'event_type', 'created_at'], name='taller_what_empresa__idx'),
        ),
        migrations.AddIndex(
            model_name='whatsappadminnotification',
            index=models.Index(fields=['comprobante_pago'], name='taller_what_comprob_idx'),
        ),
        migrations.AddIndex(
            model_name='whatsappadminnotification',
            index=models.Index(fields=['pago_pendiente'], name='taller_what_pago_pe_idx'),
        ),
    ]
