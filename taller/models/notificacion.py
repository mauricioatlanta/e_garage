# taller/models/notificacion.py - Sistema de Notificaciones
"""
Modelo para gestionar notificaciones automáticas del sistema
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .empresa import Empresa
from .clientes import Cliente
from .vehiculos import Vehiculo
from .documento import Documento

class TipoNotificacion(models.Model):
    """Tipos de notificaciones disponibles"""
    
    TIPOS = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
        ('PUSH', 'Push Notification'),
        ('SISTEMA', 'Notificación del Sistema'),
    ]
    
    EVENTOS = [
        ('DOCUMENTO_CREADO', 'Documento Creado'),
        ('SUSCRIPCION_VENCE', 'Suscripción por Vencer'),
        ('SUSCRIPCION_VENCIDA', 'Suscripción Vencida'),
        ('MANTENIMIENTO_RECORDATORIO', 'Recordatorio de Mantenimiento'),
        ('REVISION_VEHICULO', 'Revisión de Vehículo'),
        ('PAGO_PENDIENTE', 'Pago Pendiente'),
        ('CLIENTE_INACTIVO', 'Cliente Inactivo'),
        ('BACKUP_COMPLETADO', 'Backup Completado'),
        ('ERROR_SISTEMA', 'Error del Sistema'),
    ]
    
    nombre = models.CharField(max_length=100)
    evento = models.CharField(max_length=50, choices=EVENTOS)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    activo = models.BooleanField(default=True)
    template_asunto = models.CharField(max_length=200)
    template_mensaje = models.TextField()
    dias_anticipacion = models.PositiveIntegerField(default=0, help_text="Días de anticipación para el recordatorio")
    
    class Meta:
        verbose_name = "Tipo de Notificación"
        verbose_name_plural = "Tipos de Notificaciones"
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

class NotificacionEnviada(models.Model):
    """Registro de notificaciones enviadas"""
    
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('ERROR', 'Error'),
        ('REINTENTO', 'Reintento'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo_notificacion = models.ForeignKey(TipoNotificacion, on_delete=models.CASCADE)
    destinatario_email = models.EmailField(blank=True)
    destinatario_telefono = models.CharField(max_length=20, blank=True)
    destinatario_nombre = models.CharField(max_length=100)
    
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    
    # Referencias opcionales
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    intentos = models.PositiveIntegerField(default=0)
    fecha_programada = models.DateTimeField(default=timezone.now)
    fecha_enviado = models.DateTimeField(null=True, blank=True)
    fecha_entregado = models.DateTimeField(null=True, blank=True)
    error_mensaje = models.TextField(blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notificación Enviada"
        verbose_name_plural = "Notificaciones Enviadas"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tipo_notificacion.nombre} -> {self.destinatario_nombre} ({self.estado})"

class ConfiguracionNotificacion(models.Model):
    """Configuración de notificaciones por empresa"""
    
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='config_notificaciones')
    
    # Email settings
    email_activo = models.BooleanField(default=True)
    email_smtp_host = models.CharField(max_length=100, default='smtp.gmail.com')
    email_smtp_port = models.PositiveIntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    email_usuario = models.EmailField(blank=True)
    email_password = models.CharField(max_length=100, blank=True, help_text="Password de aplicación")
    email_remitente = models.EmailField(blank=True)
    
    # WhatsApp settings (API)
    whatsapp_activo = models.BooleanField(default=False)
    whatsapp_api_token = models.CharField(max_length=200, blank=True)
    whatsapp_numero_business = models.CharField(max_length=20, blank=True)
    
    # SMS settings
    sms_activo = models.BooleanField(default=False)
    sms_api_token = models.CharField(max_length=200, blank=True)
    sms_proveedor = models.CharField(max_length=50, default='twilio', choices=[
        ('twilio', 'Twilio'),
        ('nexmo', 'Nexmo'),
        ('local', 'Proveedor Local'),
    ])
    
    # Configuraciones generales
    notificar_documentos = models.BooleanField(default=True)
    notificar_suscripcion = models.BooleanField(default=True)
    notificar_mantenimiento = models.BooleanField(default=True)
    dias_recordatorio_suscripcion = models.PositiveIntegerField(default=7)
    dias_recordatorio_mantenimiento = models.PositiveIntegerField(default=30)
    
    # Horarios de envío (usar time objects)
    from datetime import time
    hora_inicio_envio = models.TimeField(default=time(8, 0))  # 08:00
    hora_fin_envio = models.TimeField(default=time(20, 0))    # 20:00
    enviar_fines_semana = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Notificaciones"
        verbose_name_plural = "Configuraciones de Notificaciones"
    
    def __str__(self):
        return f"Config. Notificaciones - {self.empresa.nombre_taller}"

class RecordatorioMantenimiento(models.Model):
    """Programación de recordatorios de mantenimiento"""
    
    TIPOS_MANTENIMIENTO = [
        ('ACEITE', 'Cambio de Aceite'),
        ('FRENOS', 'Revisión de Frenos'),
        ('NEUMATICOS', 'Rotación de Neumáticos'),
        ('REVISION_GENERAL', 'Revisión General'),
        ('ALINEACION', 'Alineación y Balanceo'),
        ('BATERIA', 'Revisión de Batería'),
        ('FILTROS', 'Cambio de Filtros'),
        ('BUJIAS', 'Cambio de Bujías'),
        ('CORREA_DISTRIBUCION', 'Correa de Distribución'),
        ('PERSONALIZADO', 'Mantenimiento Personalizado'),
    ]
    
    ESTADOS = [
        ('PROGRAMADO', 'Programado'),
        ('NOTIFICADO', 'Notificado'),
        ('REALIZADO', 'Realizado'),
        ('CANCELADO', 'Cancelado'),
        ('VENCIDO', 'Vencido'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE)
    documento_origen = models.ForeignKey(Documento, on_delete=models.CASCADE, null=True, blank=True)
    
    tipo_mantenimiento = models.CharField(max_length=30, choices=TIPOS_MANTENIMIENTO)
    descripcion = models.TextField()
    
    # Programación
    fecha_programada = models.DateField()
    kilometraje_programado = models.PositiveIntegerField(null=True, blank=True)
    dias_recordatorio = models.PositiveIntegerField(default=7)
    
    # Estado
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PROGRAMADO')
    fecha_realizado = models.DateField(null=True, blank=True)
    notas_realizacion = models.TextField(blank=True)
    
    # Notificaciones
    notificacion_enviada = models.BooleanField(default=False)
    fecha_notificacion = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Recordatorio de Mantenimiento"
        verbose_name_plural = "Recordatorios de Mantenimiento"
        ordering = ['fecha_programada']
    
    def __str__(self):
        return f"{self.get_tipo_mantenimiento_display()} - {self.vehiculo} ({self.fecha_programada})"
    
    @property
    def dias_hasta_mantenimiento(self):
        """Días restantes hasta el mantenimiento"""
        if self.fecha_programada:
            return (self.fecha_programada - timezone.now().date()).days
        return None
    
    @property
    def requiere_notificacion(self):
        """Verifica si requiere notificación"""
        dias_restantes = self.dias_hasta_mantenimiento
        return (
            not self.notificacion_enviada and 
            self.estado == 'PROGRAMADO' and
            dias_restantes is not None and
            dias_restantes <= self.dias_recordatorio
        )
