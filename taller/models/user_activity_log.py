from django.db import models
from django.conf import settings

class UserActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_logs")
    empresa = models.ForeignKey("taller.Empresa", on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10, default="GET")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Actividad de usuario"
        verbose_name_plural = "Actividades de usuarios"

    def __str__(self):
        return f"{self.user.username} -> {self.path} ({self.created_at.strftime('%H:%M:%S')})"
