"""
Servicios de negocio para eGarage (lógica transversal de reportes/dashboards)

Este módulo contiene servicios reutilizables para:
- Dashboards y métricas (DashboardService)
- Generación de documentos (DocumentOutputService)
- Registro de usuarios y embudo (RegistrationService, registro_embudo_service)

Inventario: importar directamente desde taller.services.inventory_service.
"""

from .dashboard_service import DashboardService
from .document_output_service import DocumentOutputService
from .registration_service import RegistrationService

from taller.services.inventory_service import InventoryService

__all__ = [
    "InventoryService",
    "DocumentOutputService",
    "DashboardService",
    "RegistrationService",
]
