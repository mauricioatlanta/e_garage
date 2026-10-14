from django.db import models
from taller.models.compatibility import PartApplication
from taller.models.pieza_desarme import PiezaDesarme

class CompatibilityService:

    @staticmethod
    def find_parts_for_vehicle(marca: str, modelo: str, anio: int = None, motor: str = None):
        """
        Dado un vehículo, retorna los códigos de piezas o repuestos compatibles
        registrados en el sistema, sin importar de qué auto original fueron desmontados.
        """
        qs = PartApplication.objects.filter(activo=True, marca__iexact=marca, modelo__iexact=modelo)
        
        if anio:
            qs = qs.filter(
                models.Q(anio_desde__lte=anio) | models.Q(anio_desde__isnull=True),
                models.Q(anio_hasta__gte=anio) | models.Q(anio_hasta__isnull=True)
            )
            
        codigos = qs.values_list('codigo_pieza', flat=True).distinct()
        # Usamos estado_pieza tal como está definido en PiezaDesarme
        return PiezaDesarme.objects.filter(codigo__in=codigos, estado_pieza='disponible', activo=True, publicada=True)

    @staticmethod
    def find_compatible_vehicles_for_part(codigo_pieza: str):
        """
        Dada una pieza en estante, lista todos los vehículos alternativos 
        a los que les hace 'fit'.
        """
        return PartApplication.objects.filter(codigo_pieza__iexact=codigo_pieza, activo=True)
