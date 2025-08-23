
from django.db import models
from django.urls import reverse
from core.models import TenantScoped, TenantManager
from .marca import Marca
from .modelo import Modelo
from .clientes import Cliente
from .extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo


class Vehiculo(TenantScoped):
    # empresa viene de TenantScoped (inicialmente nullable en migración)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True)
    patente = models.CharField(max_length=20, db_index=True)
    anio = models.PositiveIntegerField(verbose_name="Año")
    color = models.ForeignKey(ColorVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    vin = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    motor = models.ForeignKey(MotorVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    caja = models.ForeignKey(CajaVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    millas = models.PositiveIntegerField(blank=True, null=True, verbose_name='Millas/Kilometraje')

    objects = TenantManager()

    def __str__(self):
        return f"{self.patente} - {self.modelo}"

    def get_absolute_url(self):  # usado por CreateView en tests
        try:
            return reverse('vehiculos:ver_vehiculo', args=[self.pk])
        except Exception:
            return "/vehiculos-core/"  # fallback seguro

    class Meta(TenantScoped.Meta):
        ordering = ['marca', 'modelo', 'patente']
        verbose_name = "Vehículo"
        indexes = [
            models.Index(fields=["empresa"]),
            models.Index(fields=["empresa", "patente"]),
            models.Index(fields=["empresa", "vin"]),
        ]
