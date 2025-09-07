from django.db import models


class PrecioSuscripcion(models.Model):
    """Modelo para manejar precios de suscripciones por país"""

    TIPOS_PLAN = [
        ("mensual", "Mensual"),
        ("semestral", "Semestral"),
        ("anual", "Anual"),
    ]

    PAISES = [
        ("CL", "Chile"),
        ("US", "Estados Unidos"),
    ]

    tipo_plan = models.CharField(max_length=20, choices=TIPOS_PLAN)
    pais = models.CharField(max_length=2, choices=PAISES)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default="CLP")
    activo = models.BooleanField(default=True)

    # Metadatos del plan
    nombre_plan = models.CharField(max_length=100, default="Plan Estándar")
    descripcion = models.TextField(blank=True)

    # Características incluidas
    documentos_ilimitados = models.BooleanField(default=True)
    usuarios_incluidos = models.IntegerField(default=5)
    soporte_prioritario = models.BooleanField(default=True)
    reportes_avanzados = models.BooleanField(default=True)
    diagnostico_ia = models.BooleanField(default=True)
    api_incluida = models.BooleanField(default=False)
    multisucursal = models.BooleanField(default=False)

    class Meta:
        unique_together = ["tipo_plan", "pais"]
        verbose_name = "Precio de Suscripción"
        verbose_name_plural = "Precios de Suscripciones"
        ordering = ["pais", "tipo_plan"]

    def __str__(self):
        return f"{self.get_pais_display()} - {self.get_tipo_plan_display()}: {self.precio} {self.moneda}"

    def precio_formateado(self):
        """Retorna el precio formateado según el país"""
        if self.pais == "US":
            return f"${self.precio:,.2f} USD"
        else:
            return f"${self.precio:,.0f} CLP"

    def caracteristicas_list(self):
        """Retorna lista de características incluidas en el plan"""
        caracteristicas = []

        if self.documentos_ilimitados:
            caracteristicas.append("Documentos ilimitados")

        if self.usuarios_incluidos > 0:
            caracteristicas.append(f"Hasta {self.usuarios_incluidos} usuarios")

        if self.reportes_avanzados:
            caracteristicas.append("Reportes avanzados")

        if self.diagnostico_ia:
            caracteristicas.append("Diagnóstico IA incluido")

        if self.soporte_prioritario:
            caracteristicas.append("Soporte prioritario")

        if self.api_incluida:
            caracteristicas.append("API personalizada")

        if self.multisucursal:
            caracteristicas.append("Multi-sucursales")

        return caracteristicas
