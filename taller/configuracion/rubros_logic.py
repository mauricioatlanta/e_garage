"""
Helpers centralizados para lógica basada en rubros.
"""

from taller.configuracion.rubros_responsables import (
    DEFAULT_RESPONSABLE_LABEL,
    RESPONSABLE_LABEL_POR_RUBRO,
)
from taller.models.tecnico import Tecnico


DEFAULT_ROLES = ['TECNICO', 'VENDEDOR', 'MIXTO']

ROLES_POR_RUBRO = {
    "WORKSHOP": ['TECNICO', 'MIXTO'],
    "WORKSHOP_MOTO": ['TECNICO', 'MIXTO'],
    "WORKSHOP_HEAVY": ['TECNICO', 'MIXTO'],
    "EXHAUST": ['TECNICO', 'MIXTO'],
    "BODYSHOP": ['TECNICO', 'MIXTO'],
    "ELECTRIC": ['TECNICO', 'MIXTO'],
    "TIRE": ['TECNICO', 'MIXTO'],
    "PARTS": ['VENDEDOR', 'MIXTO'],
    "DETAILING": ['TECNICO', 'VENDEDOR', 'MIXTO'],
    "GLASS_AUDIO": ['TECNICO', 'VENDEDOR', 'MIXTO'],
    "FLEET": ['TECNICO', 'MIXTO'],
    "MIXED": ['TECNICO', 'VENDEDOR', 'MIXTO'],
}


def get_responsable_label(config):
    """Devuelve la etiqueta del responsable según la configuración."""
    if config:
        return config.get_responsable_label()
    return DEFAULT_RESPONSABLE_LABEL


def get_roles_permitidos(config):
    """Devuelve los roles permitidos para el campo técnico responsable."""
    rubro = getattr(config, "rubro_principal", None)
    if not rubro:
        return DEFAULT_ROLES
    return ROLES_POR_RUBRO.get(rubro, DEFAULT_ROLES)


def get_ui_config(config):
    """Devuelve la configuración de UI para el formulario de documentos."""
    if config and hasattr(config, "get_ui_config"):
        return config.get_ui_config()
    return {
        "show_vehicle": True,
        "show_services": True,
        "show_otros_servicios": True,
        "show_repuestos": True,
        "show_kilometraje": False,
    }



