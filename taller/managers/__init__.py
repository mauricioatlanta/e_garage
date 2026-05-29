"""
Managers personalizados para aislamiento multi-tenant.
"""

from .empresa_aware import (
    EmpresaAwareManager,
    EmpresaAwareManagerStrict,
    EmpresaAwareQuerySet,
    EmpresaAwareDefaultManager,
)

__all__ = [
    "EmpresaAwareManager",
    "EmpresaAwareManagerStrict",
    "EmpresaAwareQuerySet",
    "EmpresaAwareDefaultManager",
]
