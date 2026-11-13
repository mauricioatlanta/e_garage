from decimal import Decimal
from django.db import models
from django.db.models import Index
from core.models import TenantScoped

class Tire(TenantScoped):
    TIPO_CHOICES = [
        ("Nuevo", "Nuevo"),
        ("Usado", "Usado"),
        ("Recapado", "Recapado"),
    ]
    USO_CHOICES = [
        ("Ciudad", "Ciudad"),
        ("Carretera", "Carretera"),
        ("HT", "HT - Highway Terrain"),
        ("AT", "AT - All Terrain"),
        ("MT", "MT - Mud Terrain"),
        ("All Season", "All Season"),
    ]
    # Medida en 3 campos separados - NUNCA texto libre
    ancho = models.PositiveIntegerField(help_text="Ej: 175")
    perfil = models.PositiveIntegerField(help_text="Ej: 70")
    aro = models.PositiveIntegerField(help_text="Ej: 14 -> se muestra como R14")
    marca = models.CharField(max_length=80, db_index=True)
    modelo = models.CharField(max_length=80, blank=True, default="")
    indice = models.CharField(max_length=10, blank=True, default="", help_text="Ej: 88H, 91V")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="Nuevo", db_index=True)
    uso = models.CharField(max_length=20, choices=USO_CHOICES, default="Ciudad")
    dot = models.CharField(max_length=20, blank=True, default="", help_text="DOT / Año fabricación")
    cantidad_stock = models.PositiveIntegerField(default=0)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    precio_instalado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), help_text="Venta + montaje + balanceo")
    proveedor = models.CharField(max_length=200, null=True, blank=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Neumático"
        verbose_name_plural = "Neumáticos"
        indexes = [
            Index(fields=["empresa", "ancho", "perfil", "aro"]),
            Index(fields=["empresa", "marca"]),
            Index(fields=["empresa", "tipo"]),
        ]

    @property
    def medida(self):
        return f"{self.ancho}/{self.perfil} R{self.aro}"

    def __str__(self):
        return f"{self.medida} {self.tipo} {self.marca} {self.modelo}"
