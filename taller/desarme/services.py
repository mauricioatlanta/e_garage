"""
Servicios del módulo Desarme.
El catálogo usado depende del país de la empresa: USA → catálogo USA; resto → legacy.
"""
from taller.models.pieza_desarme import PiezaDesarme

from .catalogo_operativo import get_catalogo_operativo_desarme


def generar_inventario_vehiculo(vehiculo, empresa):
    """
    Genera piezas de inventario para un vehículo de desarme a partir del catálogo operativo.
    USA (empresa.pais='US') → catálogo USA (engine_assembly, alternator, etc.).
    Resto → catálogo legacy (MOT-01, CAR-01, etc.).
    Retorna el número de piezas creadas (solo las nuevas, no las ya existentes).
    """
    if vehiculo.tipo_uso != "DESARME":
        return 0

    catalogo = get_catalogo_operativo_desarme(empresa)
    count = 0
    for item in catalogo:
        codigo = item["codigo"]
        nombre = item["nombre"]
        zona = item["zona"]
        precio_base = item["precio_base"]
        _, created = PiezaDesarme.objects.get_or_create(
            vehiculo=vehiculo,
            codigo=codigo,
            defaults={
                "empresa": empresa,
                "nombre": nombre,
                "zona": zona,
                "estado_pieza": "DISPONIBLE",
                "precio_venta_sugerido": precio_base,
                "cantidad": 1,
                "activo": True,
            },
        )
        if created:
            count += 1
    return count
