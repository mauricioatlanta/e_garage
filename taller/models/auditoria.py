# models/auditoria.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .empresa import Empresa

class LogAuditoria(models.Model):
    ACCIONES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Modificar'),
        ('DELETE', 'Eliminar'),
        ('VIEW', 'Ver'),
        ('LOGIN', 'Iniciar Sesión'),
        ('LOGOUT', 'Cerrar Sesión'),
        ('EXPORT', 'Exportar'),
        ('PRINT', 'Imprimir'),
    ]
    
    MODELOS = [
        ('DOCUMENTO', 'Documento'),
        ('CLIENTE', 'Cliente'),
        ('VEHICULO', 'Vehículo'),
        ('REPUESTO', 'Repuesto'),
        ('SERVICIO', 'Servicio'),
        ('USUARIO', 'Usuario'),
        ('EMPRESA', 'Empresa'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=10, choices=ACCIONES)
    modelo = models.CharField(max_length=20, choices=MODELOS)
    objeto_id = models.PositiveIntegerField(null=True, blank=True)
    descripcion = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    fecha_hora = models.DateTimeField(default=timezone.now)
    datos_antes = models.JSONField(null=True, blank=True, help_text="Estado anterior del objeto")
    datos_despues = models.JSONField(null=True, blank=True, help_text="Estado posterior del objeto")
    
    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.accion} {self.modelo} [{self.fecha_hora}]"
    
    @classmethod
    def log_accion(cls, usuario, empresa, accion, modelo, objeto_id=None, 
                   descripcion="", request=None, datos_antes=None, datos_despues=None):
        """Método helper para crear logs de auditoría"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return cls.objects.create(
            empresa=empresa,
            usuario=usuario,
            accion=accion,
            modelo=modelo,
            objeto_id=objeto_id,
            descripcion=descripcion,
            ip_address=ip_address,
            user_agent=user_agent,
            datos_antes=datos_antes,
            datos_despues=datos_despues
        )
    
    @staticmethod
    def get_client_ip(request):
        """Obtener IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
