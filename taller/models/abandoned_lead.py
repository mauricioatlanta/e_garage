from django.db import models
from django.utils import timezone


class AbandonedLead(models.Model):
    nombre = models.CharField(max_length=160, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    rubro = models.CharField(max_length=80, blank=True, db_index=True)
    pais = models.CharField(max_length=8, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    contactado = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = "Lead abandonado"
        verbose_name_plural = "Leads abandonados"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["contactado", "fecha_creacion"]),
            models.Index(fields=["pais", "rubro", "fecha_creacion"]),
        ]

    def __str__(self):
        return self.nombre or self.email or self.whatsapp or f"Lead #{self.pk}"

    @property
    def whatsapp_url(self):
        digits = "".join(ch for ch in (self.whatsapp or "") if ch.isdigit())
        if not digits:
            return ""
        return f"https://wa.me/{digits}"
