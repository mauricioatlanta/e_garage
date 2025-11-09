"""
eGarage - Sistema de Gestión de Talleres Automotrices
Version Management
"""

__version__ = "2.1.0"
__version_info__ = (2, 1, 0)
__release_date__ = "2025-11-08"

# Changelog de esta versión
CHANGELOG = """
Version 2.1.0 (2025-11-08)
==========================

🎨 Sistema de Branding Unificado
---------------------------------
✅ Context processor con objeto BRAND centralizado
✅ Logo del suscriptor visible en todas las páginas
✅ Prioridad: CompanySettings → ConfiguracionEmpresa → Empresa
✅ Template include reusable para headers
✅ Variables CSS dinámicas basadas en branding

📄 Mejoras en Documentos
-------------------------
✅ Campo "numero" ahora se autogenera automáticamente
✅ No es obligatorio en el formulario
✅ URL api_next_number agregada para compatibilidad
✅ Validaciones mejoradas

🔧 Fixes y Optimizaciones
--------------------------
✅ Eliminadas referencias rotas a debug_urls
✅ Caché de branding mejorado
✅ Compatibilidad backwards con código existente
✅ Sistema de fallbacks robusto

🌐 Soporte Multi-idioma
------------------------
✅ Templates compatibles con ES/EN
✅ Centro de Operaciones Espacial (USA) optimizado
✅ Dashboard unificado Chile/USA
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
