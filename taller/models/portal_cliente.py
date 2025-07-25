
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .cliente import Cliente
from .empresa import Empresa
from .vehiculos import Vehiculo
from .documento import Documento

class ClienteUsuario(models.Model):
    """Vinculación entre Cliente y User de Django para el portal"""
    
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='usuario_portal')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente_portal')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    # Preferencias del portal
    recibir_notificaciones = models.BooleanField(default=True)
    idioma = models.CharField(max_length=10, default='es', choices=[
        ('es', 'Español'),
        ('en', 'English'),
    ])
    
    class Meta:
        verbose_name = "Usuario Cliente Portal"
        verbose_name_plural = "Usuarios Cliente Portal"
        db_table = 'taller_cliente_usuario'
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.user.username}"

class SolicitudPresupuesto(models.Model):
    """Solicitudes de presupuesto desde el portal de clientes"""
    
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En Revisión'),
        ('PRESUPUESTADO', 'Presupuestado'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    PRIORIDADES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]
    
    # Información básica
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    
    # Detalles de la solicitud
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='MEDIA')
    fecha_deseada = models.DateField(null=True, blank=True, help_text="Fecha deseada para el servicio")
    
    # Estado y seguimiento
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    numero_solicitud = models.CharField(max_length=50, unique=True, blank=True)
    
    # Respuesta del taller
    presupuesto_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tiempo_estimado = models.CharField(max_length=100, blank=True, help_text="Ej: 2-3 días")
    respuesta_taller = models.TextField(blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    usuario_respuesta = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Documento generado (si se aprueba)
    documento_generado = models.ForeignKey(Documento, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solicitud de Presupuesto"
        verbose_name_plural = "Solicitudes de Presupuesto"
        ordering = ['-created_at']
        db_table = 'taller_solicitud_presupuesto'
    
    def save(self, *args, **kwargs):
        if not self.numero_solicitud:
            from datetime import datetime
            self.numero_solicitud = f"SOL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_solicitud} - {self.cliente.nombre}"

class PortalConfiguracion(models.Model):
    """Configuración del portal de clientes por empresa"""
    
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='portal_config')
    
    # Configuración general
    portal_activo = models.BooleanField(default=True)
    titulo_portal = models.CharField(max_length=100, default="Portal de Clientes")
    mensaje_bienvenida = models.TextField(default="Bienvenido a nuestro portal de clientes")
    
    # Funcionalidades habilitadas
    permitir_solicitud_presupuestos = models.BooleanField(default=True)
    permitir_ver_documentos = models.BooleanField(default=True)
    permitir_ver_vehiculos = models.BooleanField(default=True)
    permitir_descargar_documentos = models.BooleanField(default=False)
    
    # Configuración visual
    color_primario = models.CharField(max_length=7, default="#007bff")
    color_secundario = models.CharField(max_length=7, default="#6c757d")
    logo_url = models.URLField(blank=True)
    
    # Configuración de notificaciones
    notificar_nuevas_solicitudes = models.BooleanField(default=True)
    email_notificaciones = models.EmailField(blank=True)
    
    # Horarios de atención
    horario_atencion = models.TextField(default="Lunes a Viernes: 8:00 - 18:00")
    telefono_contacto = models.CharField(max_length=20, blank=True)
    email_contacto = models.EmailField(blank=True)
    
    class Meta:
        verbose_name = "Configuración Portal"
        verbose_name_plural = "Configuraciones Portal"
        db_table = 'taller_portal_configuracion'
    
    def __str__(self):
        return f"Portal {self.empresa.nombre_taller}"

class AccesoPortal(models.Model):
    """Registro de accesos al portal de clientes"""
    
    cliente_usuario = models.ForeignKey(ClienteUsuario, on_delete=models.CASCADE)
    fecha_acceso = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Actividad realizada
    pagina_visitada = models.CharField(max_length=200, blank=True)
    accion_realizada = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Acceso Portal"
        verbose_name_plural = "Accesos Portal"
        ordering = ['-fecha_acceso']
        db_table = 'taller_acceso_portal'
    
    def __str__(self):
        return f"{self.cliente_usuario.cliente.nombre} - {self.fecha_acceso.strftime('%Y-%m-%d %H:%M')}"
