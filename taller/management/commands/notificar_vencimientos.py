from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from taller.models.empresa import Empresa
from datetime import timedelta


class Command(BaseCommand):
    """
    Comando para enviar notificaciones de vencimiento de suscripción
    Ejecutar diariamente con cron: python manage.py notificar_vencimientos
    """
    help = 'Envía notificaciones de vencimiento de suscripción'
    
    def handle(self, *args, **options):
        self.stdout.write("🔔 Iniciando verificación de suscripciones...")
        
        hoy = timezone.now()
        
        # Empresas que vencen en 5 días
        empresas_5_dias = Empresa.objects.filter(
            fecha_fin__date=hoy.date() + timedelta(days=5),
            notificacion_5_dias=False,
            suscripcion_activa=True
        )
        
        # Empresas que vencen mañana
        empresas_1_dia = Empresa.objects.filter(
            fecha_fin__date=hoy.date() + timedelta(days=1),
            notificacion_1_dia=False,
            suscripcion_activa=True
        )
        
        # Empresas que vencieron hoy
        empresas_vencidas = Empresa.objects.filter(
            fecha_fin__date=hoy.date(),
            notificacion_vencido=False,
            suscripcion_activa=True
        )
        
        # Enviar notificaciones
        count_5_dias = self.enviar_notificacion_5_dias(empresas_5_dias)
        count_1_dia = self.enviar_notificacion_1_dia(empresas_1_dia)
        count_vencidas = self.enviar_notificacion_vencido(empresas_vencidas)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Notificaciones enviadas: {count_5_dias} (5 días), {count_1_dia} (1 día), {count_vencidas} (vencidas)"
            )
        )
    
    def enviar_notificacion_5_dias(self, empresas):
        count = 0
        for empresa in empresas:
            try:
                subject = "⚠️ Tu suscripción a eGarage vence en 5 días"
                message = f"""
Hola {empresa.user.first_name or empresa.user.username},

Tu suscripción a eGarage para {empresa.nombre_taller} vencerá en 5 días.

📅 Fecha de vencimiento: {empresa.fecha_expiracion.strftime('%d/%m/%Y')}
📦 Plan actual: {empresa.get_plan_display()}

Para renovar tu suscripción:
1. Ingresa a tu panel de administración
2. Ve a la sección de pagos
3. Sube tu comprobante de pago

¿Necesitas ayuda? Contáctanos por WhatsApp:
https://wa.me/56912345678

Equipo eGarage
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [empresa.user.email],
                    fail_silently=False,
                )
                
                empresa.notificacion_5_dias = True
                empresa.save()
                count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error enviando email a {empresa.nombre_taller}: {e}")
                )
        
        return count
    
    def enviar_notificacion_1_dia(self, empresas):
        count = 0
        for empresa in empresas:
            try:
                subject = "🚨 Tu suscripción a eGarage vence MAÑANA"
                message = f"""
URGENTE - {empresa.user.first_name or empresa.user.username},

Tu suscripción a eGarage para {empresa.nombre_taller} vence MAÑANA.

📅 Fecha de vencimiento: {empresa.fecha_expiracion.strftime('%d/%m/%Y')}
📦 Plan actual: {empresa.get_plan_display()}

⚠️ Si no renuevas antes del vencimiento, perderás acceso al sistema.

RENUEVA AHORA:
1. Haz tu transferencia bancaria
2. Sube el comprobante en tu panel
3. Te reactivamos en 24-48 horas

Datos bancarios:
- Banco Estado
- Cuenta: 123-456-789
- RUT: 12.345.678-9
- Titular: Atlanta Reciclajes SPA

¿Necesitas ayuda urgente? WhatsApp:
https://wa.me/56912345678

Equipo eGarage
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [empresa.user.email],
                    fail_silently=False,
                )
                
                empresa.notificacion_1_dia = True
                empresa.save()
                count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error enviando email a {empresa.nombre_taller}: {e}")
                )
        
        return count
    
    def enviar_notificacion_vencido(self, empresas):
        count = 0
        for empresa in empresas:
            try:
                subject = "❌ Tu suscripción a eGarage ha vencido"
                message = f"""
{empresa.user.first_name or empresa.user.username},

Tu suscripción a eGarage para {empresa.nombre_taller} ha vencido hoy.

El acceso al sistema ha sido suspendido hasta que renueves tu suscripción.

Para reactivar tu cuenta:
1. Realiza tu pago por transferencia bancaria
2. Sube el comprobante en el panel de suspensión
3. Te reactivamos en 24-48 horas

No perderás tus datos - están seguros y se reactivarán cuando renueves.

Datos bancarios:
- Banco Estado  
- Cuenta: 123-456-789
- RUT: 12.345.678-9
- Titular: Atlanta Reciclajes SPA

¿Necesitas ayuda? Contáctanos:
📱 WhatsApp: https://wa.me/56912345678
📧 Email: suscripcion@atlantareciclajes.cl

Equipo eGarage
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [empresa.user.email],
                    fail_silently=False,
                )
                
                empresa.notificacion_vencido = True
                empresa.save()
                count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error enviando email a {empresa.nombre_taller}: {e}")
                )
        
        return count
