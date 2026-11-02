"""
Modelos para eGarage Air - WhatsApp v2 Final
"""
from django.db import models
from django.utils import timezone


class EmpresaWhatsAppConfig(models.Model):
    """
    Configuración de WhatsApp para cada empresa.
    Permite configurar el número de teléfono de Meta y el operador autorizado.
    """
    empresa = models.OneToOneField(
        'taller.Empresa',
        on_delete=models.CASCADE,
        related_name='whatsapp_config'
    )
    phone_number_id = models.CharField(
        max_length=50,
        help_text="ID del número de teléfono en Meta Cloud API"
    )
    allowed_operator_phone = models.CharField(
        max_length=20,
        help_text="Teléfono del operador autorizado (formato: 56912345678)"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Activar/desactivar integración WhatsApp"
    )
    # Flags de funcionalidad
    enable_audio = models.BooleanField(
        default=True,
        help_text="Habilitar procesamiento de audios con IA"
    )
    enable_ocr = models.BooleanField(
        default=True,
        help_text="Habilitar reconocimiento de patentes por OCR"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'whatsapp'
        verbose_name = "Configuración WhatsApp Empresa"
        verbose_name_plural = "Configuraciones WhatsApp Empresas"
        db_table = 'whatsapp_empresa_config'

    def __str__(self):
        return f"WhatsApp Config - {self.empresa.nombre_taller}"


class WhatsAppSession(models.Model):
    """
    Sesión de conversación activa para un operador.
    Mantiene el estado de la máquina de estados y el contexto de la conversación.
    """
    # Estados posibles de la máquina de estados
    ESTADO_CHOICES = [
        ('IDLE', 'Inactivo'),
        ('WAITING_PLATE', 'Esperando Patente'),
        ('WAITING_MILEAGE', 'Esperando Kilometraje'),
        ('WAITING_ACTION', 'Esperando Acción'),
        ('WAITING_CONFIRM', 'Esperando Confirmación'),
    ]

    operator_phone = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="Teléfono del operador (formato: 56912345678)"
    )
    empresa = models.ForeignKey(
        'taller.Empresa',
        on_delete=models.CASCADE,
        related_name='whatsapp_sessions'
    )
    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES,
        default='IDLE',
        db_index=True
    )
    contexto = models.JSONField(
        default=dict,
        help_text="Contexto de la conversación: documento_id, vehiculo_id, cliente_id, etc."
    )
    last_interaction = models.DateTimeField(
        auto_now=True,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'whatsapp'
        verbose_name = "Sesión WhatsApp"
        verbose_name_plural = "Sesiones WhatsApp"
        db_table = 'whatsapp_sessions'
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['last_interaction']),
        ]

    def is_expired(self):
        """
        Verificar si la sesión ha expirado (TTL de 30 minutos).
        """
        if not self.last_interaction:
            return True
        delta = timezone.now() - self.last_interaction
        return delta.total_seconds() > 1800  # 30 minutos

    def reset(self):
        """Resetear sesión a estado inicial"""
        self.estado = 'IDLE'
        self.contexto = {}
        self.save()

    def __str__(self):
        return f"Session {self.operator_phone} - {self.estado}"
