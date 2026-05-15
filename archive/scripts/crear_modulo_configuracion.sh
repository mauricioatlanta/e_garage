#!/bin/bash
# Script para crear el módulo taller.configuracion en el servidor
# Ejecutar en el servidor desde el directorio raíz del proyecto

echo "🔧 Creando módulo taller.configuracion..."

# Directorio base del proyecto (ajustar según tu configuración)
PROJECT_DIR="/home/atlantareciclajes/apps/egarage/current"
CONFIG_DIR="$PROJECT_DIR/taller/configuracion"

# Crear directorio si no existe
mkdir -p "$CONFIG_DIR"

# Crear __init__.py
cat > "$CONFIG_DIR/__init__.py" << 'EOF'
"""
Módulo de configuración para rubros y reglas de negocio específicas por rubro.
"""
EOF

# Crear rubros_responsables.py
cat > "$CONFIG_DIR/rubros_responsables.py" << 'EOF'
"""
Configuración de etiquetas de responsable según el rubro de la empresa.

Este módulo centraliza el mapeo entre rubros y las etiquetas que deben mostrarse
en el campo "responsable" del formulario de documentos.
"""

# Mapa de etiquetas de responsable por rubro
RESPONSABLE_LABEL_POR_RUBRO = {
    # Talleres
    "WORKSHOP": "Mecánico responsable",
    "WORKSHOP_MOTO": "Mecánico responsable",
    "WORKSHOP_HEAVY": "Mecánico responsable",
    "EXHAUST": "Mecánico responsable",
    "BODYSHOP": "Mecánico responsable",
    "ELECTRIC": "Técnico responsable",
    "TIRE": "Técnico responsable",
    # Casa de repuestos
    "PARTS": "Vendedor responsable",
    # Otros rubros
    "DETAILING": "Técnico responsable",
    "GLASS_AUDIO": "Técnico responsable",
    "FLEET": "Técnico responsable de flota",
    "MIXED": "Responsable",
}

# Etiqueta por defecto si el rubro no está en el mapa
DEFAULT_RESPONSABLE_LABEL = "Responsable"
EOF

# Crear rubros_logic.py
cat > "$CONFIG_DIR/rubros_logic.py" << 'EOF'
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
        "show_technician": True,
        "show_client": True,
    }
EOF

# Establecer permisos
chmod 644 "$CONFIG_DIR"/*.py

echo "✅ Directorio creado: $CONFIG_DIR"
echo "✅ Archivos creados:"
echo "   - __init__.py"
echo "   - rubros_responsables.py"
echo "   - rubros_logic.py"
echo ""
echo "📋 Verificación:"
ls -la "$CONFIG_DIR"
echo ""
echo "✅ Módulo creado exitosamente!"
echo ""
echo "🔍 Para verificar que funciona, ejecuta:"
echo "   cd $PROJECT_DIR"
echo "   python manage.py shell"
echo "   >>> from taller.configuracion.rubros_logic import get_responsable_label"
echo "   >>> exit()"

