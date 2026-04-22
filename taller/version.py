"""
eGarage - Sistema de Gestión de Talleres Automotrices
Version Management
"""

__version__ = "2.2.1"
__version_info__ = (2, 2, 1)
__release_date__ = "2026-04-21"

# Changelog de esta versión
CHANGELOG = """
Version 2.1.2 (2025-12-08)
==========================

🎁 Sistema de Cortesías con Auditoría Interna
---------------------------------------------
✅ Interfaz administrativa para otorgar extensiones de plan
✅ Notificaciones automáticas al cliente (Email + WhatsApp)
✅ Sistema de auditoría con notificaciones a administrador
✅ Registro completo en LogAuditoria para trazabilidad
✅ Protección de seguridad con @staff_member_required

🐛 Fix Crítico: Bug de Contraseña en iOS
------------------------------------------
✅ Corrección del bug que impedía escribir contraseñas en iPhone
✅ Implementación de ios-password-fix.js con atributos correctos
✅ Solución para campos de contraseña en login y registro
✅ Mejora significativa en tasa de conversión de usuarios iOS

📱 Implementación PWA (Progressive Web App)
--------------------------------------------
✅ Service Worker completo para funcionamiento offline
✅ Manifest.json con configuración completa de PWA
✅ Íconos optimizados para todas las resoluciones
✅ Instalación nativa en iOS y Android
✅ Experiencia de aplicación nativa mejorada

🔒 Seguridad y Gobernanza
--------------------------
✅ Auditoría automática de todas las cortesías otorgadas
✅ Notificaciones de auditoría a +56963607348
✅ Logging completo de acciones administrativas
✅ Verificación de credenciales WhatsApp mejorada

📚 Documentación
----------------
✅ Guías completas de despliegue y ejecución
✅ Checklists detallados para verificación
✅ Documentación técnica de todas las nuevas funcionalidades
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
