"""
Smart Yard - Vehicle Adapter

Normaliza VehiculoDesarme para motores de análisis.

Solo lectura.
No modifica modelos.
"""


def get_vehicle_profile(vehiculo):
    """
    Convierte VehiculoDesarme en perfil técnico estándar.
    """

    motor = (
        getattr(vehiculo, "motor_empresa_id", None)
        or getattr(vehiculo, "motor_id", None)
    )

    caja = (
        getattr(vehiculo, "caja_empresa_id", None)
        or getattr(vehiculo, "caja_id", None)
    )

    marca = getattr(vehiculo, "marca_id", None)

    modelo = getattr(vehiculo, "modelo_id", None)

    return {
        "marca_id": marca,
        "modelo_id": modelo,
        "motor_id": motor,
        "caja_id": caja,
        "anio": getattr(vehiculo, "anio", None),
        "carroceria": getattr(
            vehiculo,
            "tipo_carroceria",
            None,
        ),
    }
