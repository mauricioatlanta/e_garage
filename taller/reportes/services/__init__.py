"""
Servicios de reportes/embudo (DocumentOutput, Registration, registro_embudo).

DashboardService e InventoryService canónicos: taller.services
"""

from .document_output_service import DocumentOutputService
from .registration_service import RegistrationService

__all__ = [
    "DocumentOutputService",
    "RegistrationService",
]
