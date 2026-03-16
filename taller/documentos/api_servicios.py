"""
Wrapper de la API de servicios: delega 100% a la implementación oficial en taller/servicios/.
Mantiene la ruta documentos/api/buscar-servicios/ por compatibilidad con consumidores legacy.
Fase 5: una sola implementación oficial en servicios/api_servicios_moderno.py.
"""
from taller.servicios.api_servicios_moderno import api_buscar_servicios

__all__ = ["api_buscar_servicios"]
