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
    ("BODYSHOP", "Carrocería / Pintura"),
    ("GLASS", "Parabrisas y vidrios"),
    ("ELECTRIC", "Electricidad / Electrónica automotriz"),
    ("FLEET", "Mantención de flotas empresariales"),
    ("DESARMADURIA", "Desarmaduría / Salvage"),
    ("PARTS", "Casa de repuestos / Autopartes"),
    ("TIRE", "Vulcanización / Neumáticos y llantas"),
    ("DETAILING", "Lavado, detailing y estética"),
    ("RECYCLING", "Reciclaje / Chatarra electrónica y catalíticos"),
    ("TOWING", "Grúas y asistencia vial"),
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
