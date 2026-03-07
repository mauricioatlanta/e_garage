"""
⚠️ IMPORTANTE: Este archivo es un re-export del middleware canónico.

El middleware real está en: taller.middleware.verificar_suscripcion

Se mantiene aquí para scripts de mantenimiento que puedan importar desde tools.maintenance.
Para uso en la app Django, importa siempre desde taller.middleware.verificar_suscripcion.
"""

from taller.middleware.verificar_suscripcion import VerificarSuscripcionMiddleware

__all__ = ["VerificarSuscripcionMiddleware"]
