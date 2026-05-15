"""
Modelo para tracking del embudo de registro de suscriptores
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class RegistroEmbudoSuscriptor(models.Model):
    """
    Modelo para rastrear el embudo completo de registro de suscriptores.

    Mide:
    - Registro (formulario enviado)
    - Email confirmado
    - Primer login
    - Empresa creada (y si tuvo trial o no)
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="embudo_registro"
    )
    pais = models.CharField(max_length=5, help_text="Código de país (CL, US, MX, etc.)")

    # Fechas del embudo
    fecha_registro = models.DateTimeField(help_text="Fecha y hora en que completó el signup")
    email_confirmado_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que confirmó el email"
    )
    primer_login_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora del primer login"
    )
    empresa_creada_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que se creó la empresa"
    )

    # Info sobre trial
    obtuvo_trial = models.BooleanField(default=False, help_text="Indica si obtuvo trial de 30 días")
    trial_started_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que comenzó el trial"
    )
    trial_ends_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que termina el trial"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Embudo de Registro Suscriptor"
        verbose_name_plural = "Embudo de Registro Suscriptores"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return (
            f"Embudo: {self.user.email} ({self.pais}) - {self.fecha_registro.strftime('%Y-%m-%d')}"
        )

    @property
    def completado(self):
        """Indica si el embudo está completo (todos los pasos completados)"""
        return all([self.email_confirmado_at, self.primer_login_at, self.empresa_creada_at])

    @property
    def tasa_email_confirmado(self):
        """Tasa de conversión: email confirmado / registro"""
        return bool(self.email_confirmado_at)

    @property
    def tasa_primer_login(self):
        """Tasa de conversión: primer login / email confirmado"""
        return bool(self.primer_login_at and self.email_confirmado_at)

    @property
    def tasa_empresa_creada(self):
        """Tasa de conversión: empresa creada / primer login"""
        return bool(self.empresa_creada_at and self.primer_login_at)
