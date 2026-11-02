from django.db import models
from django.conf import settings

class SystemErrorLog(models.Model):
    ERROR_TYPE_CHOICES = [
        ("HTTP_500", "Error de Servidor (500)"),
        ("HTTP_404", "Ruta no encontrada (404)"),
        ("FORM_VALIDATION", "Error de Validación de Formulario"),
        ("GATEWAY_PAYMENT", "Fallo de Pago / Pasarela"),
    ]

    error_type = models.CharField(max_length=32, choices=ERROR_TYPE_CHOICES, db_index=True)
    status_code = models.PositiveSmallIntegerField(default=500)
    path = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    empresa = models.ForeignKey("taller.Empresa", null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=64, blank=True, default="", db_index=True)
    error_message = models.TextField(blank=True, default="")
    field_errors = models.JSONField(default=dict, blank=True)
    traceback_snippet = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Registro de Error de Sistema"
        verbose_name_plural = "Registros de Errores de Sistema"

    def __str__(self):
        return f"[{self.error_type}] {self.path} ({self.created_at:%Y-%m-%d %H:%M})"
