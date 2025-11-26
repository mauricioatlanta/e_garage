"""
eGarage - Sistema de Gestión de Talleres Automotrices
Version Management
"""

__version__ = "2.1.1"
__version_info__ = (2, 1, 1)
__release_date__ = "2025-11-25"

# Changelog de esta versión
CHANGELOG = """
Version 2.1.1 (2025-11-25)
==========================

🧹 Limpieza y Organización
---------------------------
✅ Eliminación de archivos temporales y documentación obsoleta
✅ Reorganización de estructura de templates
✅ Limpieza de archivos .py generados automáticamente
✅ Consolidación de scripts de despliegue

🔧 Mejoras y Correcciones
--------------------------
✅ Actualización de configuración de producción
✅ Mejoras en formularios de clientes y vehiculos
✅ Optimización de vistas y templates
✅ Correcciones en manejo de documentos

📦 Preparación para Despliegue
--------------------------------
✅ Scripts de actualización mejorados
✅ Documentación de despliegue actualizada
✅ Preparación para actualización en servidor PythonAnywhere
"""


def get_version():
    """Retorna la versión actual del sistema."""
    return __version__


def get_version_info():
    """Retorna información detallada de la versión."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "release_date": __release_date__,
        "changelog": CHANGELOG,
    }
