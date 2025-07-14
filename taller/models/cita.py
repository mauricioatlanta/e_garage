from django.db import models
from taller.models.clientes import Cliente

class CitaTaller(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    tipo = models.CharField(max_length=20, choices=[
        ('diagnostico', 'Diagnóstico'),
        ('ingreso', 'Ingreso'),
        ('retiro', 'Retiro')
    ])
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada')
    ], default='pendiente')
    
    
class Cita(models.Model):
    fecha = models.DateTimeField()
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    motivo = models.TextField(blank=True)

    def __str__(self):
        return f"{self.cliente} - {self.fecha}"    
