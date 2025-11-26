"""
Helpers centralizados para lógica basada en rubros.
"""

from taller.configuracion.rubros_responsables import (
    DEFAULT_RESPONSABLE_LABEL,
    RESPONSABLE_LABEL_POR_RUBRO,
)
from taller.models.tecnico import Tecnico


DEFAULT_ROLES = [Tecnico.Rol.TECNICO, Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO]

ROLES_POR_RUBRO = {
    "WORKSHOP": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "WORKSHOP_MOTO": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "WORKSHOP_HEAVY": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "EXHAUST": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "BODYSHOP": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "ELECTRIC": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "TIRE": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "PARTS": [Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO],
    "DETAILING": [Tecnico.Rol.TECNICO, Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO],
    "GLASS_AUDIO": [Tecnico.Rol.TECNICO, Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO],
    "FLEET": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "MIXED": [Tecnico.Rol.TECNICO, Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO],
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
