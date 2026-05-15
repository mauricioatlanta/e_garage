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
