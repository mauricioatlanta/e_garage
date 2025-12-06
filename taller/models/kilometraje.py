from django.db import models
from django.utils.translation import gettext_lazy as _


class KilometrajeRegistro(models.Model):
    """
    Registra el kilometraje de un vehículo en un punto específico en el tiempo,
    generalmente asociado a un Documento (OT/Presupuesto).

    Este modelo mantiene un historial inmutable del kilometraje del vehículo,
    permitiendo trazabilidad completa para reportes de garantía y análisis.
    """

    # 1. Vínculo Multi-Tenant
    # Vincula el registro a la Empresa del suscriptor (necesario para el filtrado)
    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="registros_kilometraje",
        verbose_name=_("Empresa Suscriptora"),
        db_index=True,
    )

    # 2. Vínculo de Datos
    # El vehículo al que se le registró el kilometraje
    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.CASCADE,
        related_name="historial_kilometraje",
        verbose_name=_("Vehículo"),
        db_index=True,
    )

    # 3. Vínculo de Evento (Opcional en el modelo, pero requerido en el flujo)
    # Referencia al Documento que motivó este registro (OT, Presupuesto, etc.)
    # Se hace Opcional (null=True) por si se necesita registrar un kilometraje
    # sin un documento formal, pero en tu flujo crítico será Obligatorio.
    documento = models.OneToOneField(
        "taller.Documento",
        on_delete=models.SET_NULL,  # Si se borra el Documento, NO se borra el registro de KM
        null=True,
        blank=True,
        related_name="registro_kilometraje",
        verbose_name=_("Documento Asociado"),
    )

    # 4. El Dato Clave
    kilometraje = models.PositiveIntegerField(
        verbose_name=_("Kilometraje registrado"),
        help_text=_("Kilometraje del vehículo al momento del registro"),
    )

    # 5. Auditoría
    # Usando campos explícitos para mayor claridad y control
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de registro"),
        db_index=True,
    )
    registrado_por = models.ForeignKey(
        "taller.Tecnico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_kilometraje_creados",
        verbose_name=_("Registrado por"),
    )

    class Meta:
        ordering = ["-fecha_registro"]
        verbose_name = _("Registro de Kilometraje")
        verbose_name_plural = _("Registros de Kilometraje")
        indexes = [
            models.Index(fields=["empresa", "vehiculo", "-fecha_registro"]),
            models.Index(fields=["vehiculo", "-fecha_registro"]),
            models.Index(fields=["documento"]),
        ]

    def __str__(self):
        fecha_str = self.fecha_registro.strftime("%Y-%m-%d") if self.fecha_registro else "N/A"
        return f"{self.vehiculo.patente} @ {self.kilometraje} km ({fecha_str})"

    @classmethod
    def obtener_registro_anterior(cls, vehiculo, fecha_registro):
        """
        Obtiene el registro de kilometraje anterior a una fecha dada para un vehículo.

        Args:
            vehiculo: Instancia de Vehiculo
            fecha_registro: datetime del registro actual

        Returns:
            KilometrajeRegistro o None
        """
        return (
            cls.objects.filter(vehiculo=vehiculo, fecha_registro__lt=fecha_registro)
            .order_by("-fecha_registro")
            .first()
        )

    def kilometros_recorridos_desde(self, otro_registro):
        """
        Calcula los kilómetros recorridos entre este registro y otro.

        Args:
            otro_registro: KilometrajeRegistro anterior

        Returns:
            int: Diferencia de kilometraje (puede ser negativo si el otro es más reciente)
        """
        if not otro_registro:
            return None
        return self.kilometraje - otro_registro.kilometraje

    def dias_desde_registro_anterior(self):
        """
        Calcula los días transcurridos desde el registro anterior.

        Returns:
            int o None: Días transcurridos, o None si no hay registro anterior
        """
        registro_anterior = self.obtener_registro_anterior(self.vehiculo, self.fecha_registro)
        if not registro_anterior or not registro_anterior.fecha_registro:
            return None

        delta = self.fecha_registro - registro_anterior.fecha_registro
        return delta.days
