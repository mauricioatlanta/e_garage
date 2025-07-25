from django.db import models
from .clientes import Cliente
from taller.models.vehiculos import Vehiculo  # ✅ forma correcta desde otro archivo
from taller.models.mecanico import Mecanico


class Documento(models.Model):
    TIPOS_DOCUMENTO = [
        ('Presupuesto', 'Presupuesto'),
        ('Orden de trabajo', 'Orden de trabajo'),
        ('Factura', 'Factura'),
    ]

    # Este campo conecta cada registro con la empresa dueña del dato
    empresa = models.ForeignKey('taller.Empresa', on_delete=models.CASCADE)  # Multiempresa obligatorio
    tipo_documento = models.CharField(max_length=50, choices=TIPOS_DOCUMENTO)
    numero_documento = models.CharField(max_length=50, unique=True, blank=True, null=True)
    import datetime
    fecha = models.DateField(default=datetime.date.today, blank=True, null=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    kilometraje = models.PositiveIntegerField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    mecanico = models.ForeignKey(Mecanico, on_delete=models.SET_NULL, null=True, blank=True)
    incluir_iva = models.BooleanField(default=True, verbose_name="Incluir IVA")

    def __str__(self):
        return f"{self.tipo_documento} #{self.numero_documento}"

class RepuestoDocumento(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='repuestos')
    repuesto = models.ForeignKey('taller.Repuesto', on_delete=models.PROTECT, related_name='usos_documento', null=True, blank=True)
    codigo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField()
    precio = models.PositiveIntegerField()

    @property
    def total(self):
        return self.cantidad * self.precio


class ServicioDocumento(models.Model):
    empresa = models.ForeignKey('taller.Empresa', on_delete=models.CASCADE)  # Multiempresa obligatorio
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='servicios')
    nombre = models.CharField(max_length=255)
    precio = models.PositiveIntegerField()


class OtroServicioDocumento(models.Model):
    """
    Servicios realizados por empresas externas o terceros
    """
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='otros_servicios')
    servicio = models.ForeignKey('taller.Servicio', on_delete=models.CASCADE, null=True, blank=True)
    nombre_servicio = models.CharField(max_length=255, help_text="Nombre del servicio")
    empresa_externa = models.CharField(max_length=255, help_text="Empresa que realiza el servicio")
    costo_interno = models.PositiveIntegerField(help_text="Costo pagado a la empresa externa")
    precio_cliente = models.PositiveIntegerField(help_text="Precio cobrado al cliente")
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre_servicio} - {self.empresa_externa}"

    @property
    def ganancia(self):
        """Calcula la ganancia del servicio"""
        return self.precio_cliente - self.costo_interno

    class Meta:
        verbose_name = "Otro Servicio"
        verbose_name_plural = "Otros Servicios"
