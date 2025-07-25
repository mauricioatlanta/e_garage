from django.db import models
from django.utils import timezone
from taller.models.empresa import Empresa

class ComprobantePago(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    METODO_PAGO_CHOICES = [
        ('transferencia', 'Transferencia Bancaria'),
        ('webpay', 'WebPay Plus'),
        ('paypal', 'PayPal'),
        ('mercadopago', 'MercadoPago'),
        ('otro', 'Otro'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='comprobantes')
    fecha_subida = models.DateTimeField(default=timezone.now)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='CLP')
    
    # Archivos
    comprobante = models.ImageField(upload_to='comprobantes/', help_text="Imagen del comprobante de pago")
    numero_transaccion = models.CharField(max_length=100, blank=True, help_text="Número de transacción o referencia")
    
    # Estados
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_procesado = models.DateTimeField(null=True, blank=True)
    procesado_por = models.CharField(max_length=100, blank=True)
    
    # Notas
    descripcion = models.TextField(blank=True, help_text="Descripción del pago")
    notas_admin = models.TextField(blank=True, help_text="Notas administrativas")
    
    # Configuración de plan
    plan_solicitado = models.CharField(max_length=20, choices=Empresa.PLAN_CHOICES, default='basic')
    meses_pagados = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-fecha_subida']
        verbose_name = "Comprobante de Pago"
        verbose_name_plural = "Comprobantes de Pago"

    def __str__(self):
        return f"Pago {self.empresa.nombre_taller} - ${self.monto} ({self.estado})"

    def aprobar(self, procesado_por="Sistema"):
        """Aprobar el comprobante y extender suscripción"""
        self.estado = 'aprobado'
        self.fecha_procesado = timezone.now()
        self.procesado_por = procesado_por
        
        # Extender suscripción de la empresa
        dias_extension = self.meses_pagados * 30
        self.empresa.extender_suscripcion(dias_extension)
        self.empresa.plan = self.plan_solicitado
        self.empresa.valor_mensual = self.monto / self.meses_pagados
        self.empresa.save()
        
        self.save()
        
        # Enviar notificación de aprobación
        self.enviar_notificacion_aprobacion()

    def rechazar(self, motivo="", procesado_por="Sistema"):
        """Rechazar el comprobante"""
        self.estado = 'rechazado'
        self.fecha_procesado = timezone.now()
        self.procesado_por = procesado_por
        self.notas_admin = motivo
        self.save()
        
        # Enviar notificación de rechazo
        self.enviar_notificacion_rechazo()

    def enviar_notificacion_aprobacion(self):
        """Envía notificación de que el pago fue aprobado"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"✅ Pago Aprobado - {self.empresa.nombre_taller}"
        fecha_vencimiento = self.empresa.fecha_fin.strftime('%d/%m/%Y') if self.empresa.fecha_fin else "No definida"
        plan_display = dict(self.empresa.PLAN_CHOICES).get(self.plan_solicitado, self.plan_solicitado)
        
        message = f"""
        ¡Excelente! Tu pago ha sido aprobado.
        
        Detalles:
        - Empresa: {self.empresa.nombre_taller}
        - Monto: ${self.monto} {self.moneda}
        - Plan: {plan_display}
        - Nueva fecha de vencimiento: {fecha_vencimiento}
        
        Ya puedes continuar usando eGarage sin restricciones.
        
        ¡Gracias por confiar en nosotros!
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.empresa.email, self.empresa.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando email de aprobación: {e}")

    def enviar_notificacion_rechazo(self):
        """Envía notificación de que el pago fue rechazado"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"❌ Pago Rechazado - {self.empresa.nombre_taller}"
        message = f"""
        Tu comprobante de pago ha sido rechazado.
        
        Detalles:
        - Empresa: {self.empresa.nombre_taller}
        - Monto: ${self.monto} {self.moneda}
        - Motivo: {self.notas_admin}
        
        Por favor, revisa el comprobante y vuelve a subirlo o contáctanos para más información.
        
        WhatsApp: +56 9 XXXX XXXX
        Email: suscripcion@atlantareciclajes.cl
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.empresa.email, self.empresa.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando email de rechazo: {e}")

    def enviar_notificacion_admin(self):
        """Envía notificación al admin de nuevo comprobante"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        plan_display = dict(self.empresa.PLAN_CHOICES).get(self.plan_solicitado, self.plan_solicitado)
        metodo_display = dict(self.METODO_PAGO_CHOICES).get(self.metodo_pago, self.metodo_pago)
        
        subject = f"💰 Nuevo Comprobante de Pago - {self.empresa.nombre_taller}"
        message = f"""
        Se ha subido un nuevo comprobante de pago.
        
        Detalles:
        - Empresa: {self.empresa.nombre_taller}
        - Usuario: {self.empresa.user.username} ({self.empresa.user.email})
        - Monto: ${self.monto} {self.moneda}
        - Plan solicitado: {plan_display}
        - Método de pago: {metodo_display}
        - Número transacción: {self.numero_transaccion}
        
        Revisa el comprobante en el panel de administración.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['suscripcion@atlantareciclajes.cl'],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando email al admin: {e}")

    def save(self, *args, **kwargs):
        """Al crear nuevo comprobante, enviar notificación al admin"""
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new:
            self.enviar_notificacion_admin()
