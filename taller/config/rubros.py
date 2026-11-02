# -*- coding: utf-8 -*-
"""
Constantes centralizadas para rubros de talleres.
Este archivo centraliza la definición de rubros para facilitar su mantenimiento.
"""

# Rubros disponibles para talleres
RUBROS_TALLER = [
    ("WORKSHOP", "Taller mecánico integral"),
    ("WORKSHOP_MOTO", "Taller de motos"),
    ("WORKSHOP_HEAVY", "Taller de camiones/buses"),
    ("EXHAUST", "Escapes y mufflers"),
    ("PARTS", "Casa de repuestos / Autopartes"),
    ("TIRE", "Vulcanización / Neumáticos y llantas"),
    ("BODYSHOP", "Carrocería / Pintura"),
    ("DETAILING", "Lavado, detailing y estética"),
    ("ELECTRIC", "Electricidad / electrónica automotriz"),
    ("GLASS_AUDIO", "Parabrisas, vidrios y audio / accesorios"),
    ("FLEET", "Mantención de flotas empresariales"),
    ("SUSPENSION_STEERING", "Taller de Suspensión y Dirección"),
    ("BRAKES", "Taller de Frenos"),
    ("OBD_DIAGNOSTIC", "Taller de Diagnóstico Computarizado (OBD-II)"),
    ("CLASSIC_CARS", "Taller de Reparación de Vehículos Clásicos"),
    ("AUDIO_ENTERTAINMENT", "Taller de Sistemas de Audio y Entretenimiento Automotriz"),
    ("GAS_CONVERSION", "Taller de Conversiones a Gas"),
    ("FLEET_REPAIR", "Taller de Reparación de Flotas Corporativas"),
    ("BODY_GLASS", "Taller de Carrocería y Reparación de Vidrios"),
    ("TUNING", "Taller de Tuning / Personalización"),
    ("MIXED", "Mixto (varios rubros)"),
]

# Mapeo de valores a etiquetas para fácil acceso
RUBROS_DICT = dict(RUBROS_TALLER)


def get_rubro_label(value):
    """Obtiene la etiqueta de un rubro por su valor."""
    return RUBROS_DICT.get(value, value)


def get_rubros_list():
    """Retorna una lista de valores de rubros."""
    return [value for value, label in RUBROS_TALLER]
