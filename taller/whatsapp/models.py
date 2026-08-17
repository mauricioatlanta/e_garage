"""
Modelo para tracking de notificaciones WhatsApp admin
Permite idempotencia real basada en idempotency_key único
"""
import uuid
from typing import Optional
from django.db import models
from django.utils import timezone


class WhatsAppAdminNotificationLog(models.Model):
    """
    Registro de notificaciones WhatsApp admin enviadas
    Permite idempotencia: no enviar dos veces la misma notificación
    
    🔒 IDEMPOTENCIA: Basada en idempotency_key único (empresa_id + event_type + ref_id)
    """
    # 🔒 CLAVE DE IDEMPOTENCIA (única)
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Clave única para prevenir duplicados: empresa_id:event_type:ref_id"
    )
    
    # Referencia al pago/comprobante que disparó la notificación (opcional)
    comprobante_pago = models.ForeignKey(
        "taller.ComprobantePago",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_notifications",
    )
    pago_pendiente = models.ForeignKey(
        "taller.PagoPendiente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_notifications",
    )
    
    # Referencia a la empresa
    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="whatsapp_admin_notifications",
    )
    
    # Tipo de evento
    event_type = models.CharField(
        max_length=50,
        choices=[
            ("nueva_suscripcion", "Nueva Suscripción"),
            ("renovacion", "Renovación"),
            ("cambio_plan", "Cambio de Plan"),
        ],
    )
    
    # Datos de la notificación
    plan = models.CharField(max_length=20)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Resultado del envío
    provider = models.CharField(max_length=20, default="dummy")  # "dummy" | "meta"
    success = models.BooleanField(default=False)
    message_id = models.CharField(max_length=255, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        app_label = 'taller'
        verbose_name = "Notificación WhatsApp Admin"
        verbose_name_plural = "Notificaciones WhatsApp Admin"
        # Índice único en idempotency_key (ya está en el campo)
        indexes = [
            models.Index(fields=["empresa", "event_type", "created_at"]),
            models.Index(fields=["comprobante_pago"]),
            models.Index(fields=["pago_pendiente"]),
        ]
    
    def __str__(self):
        return f"WhatsApp Admin: {self.empresa.nombre_taller} - {self.event_type} ({self.created_at})"
    
    @staticmethod
    def generate_idempotency_key(
        empresa_id: int,
        event_type: str,
        comprobante_pago_id: Optional[int] = None,
        pago_pendiente_id: Optional[int] = None,
        operation_uuid: Optional[str] = None,
    ) -> str:
        """
        Genera clave de idempotencia única
        
        Formato: empresa_id:event_type:ref_id
        - Si hay comprobante_pago_id: empresa_id:event_type:comp_{comprobante_id}
        - Si hay pago_pendiente_id: empresa_id:event_type:pago_{pago_id}
        - Si no hay ref, usar operation_uuid: empresa_id:event_type:op_{uuid}
        """
        if comprobante_pago_id:
            ref_id = f"comp_{comprobante_pago_id}"
        elif pago_pendiente_id:
            ref_id = f"pago_{pago_pendiente_id}"
        elif operation_uuid:
            ref_id = f"op_{operation_uuid}"
        else:
            # Fallback: generar UUID único para esta operación
            ref_id = f"op_{uuid.uuid4().hex[:16]}"
        
        return f"{empresa_id}:{event_type}:{ref_id}"
