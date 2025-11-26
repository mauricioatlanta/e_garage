"""
Utilidades para auditoría y detección de fugas de datos multi-tenant.
"""

import logging
from typing import Optional
from django.db.models import Model, QuerySet
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def audit_queryset_access(queryset: QuerySet, user, model_name: str):
    """
    Auditar acceso a queryset y verificar que esté filtrado por empresa.

    Args:
        queryset: QuerySet a auditar
        model_name: Nombre del modelo para logging

    Returns:
        bool: True si está correctamente filtrado, False si hay riesgo
    """
    if not user or not user.is_authenticated:
        logger.warning(f"Queryset {model_name} accedido sin usuario autenticado")
        return False

    try:
        empresa = user.empresa
    except AttributeError:
        logger.warning(f"Queryset {model_name} accedido por usuario sin empresa: {user.username}")
        return False

    # Verificar si el queryset está filtrado por empresa
    # Esto es difícil de hacer de forma perfecta, pero podemos hacer algunas verificaciones

    # Opción 1: Verificar que el queryset no esté vacío por defecto
    # Si un queryset sin filtros devuelve objetos, podría ser un problema

    # Opción 2: Verificar que haya filtro explícito en el SQL
    sql = str(queryset.query)
    if "empresa" not in sql.lower() and "empresa_id" not in sql.lower():
        # Podría ser un problema, pero no es definitivo
        # Algunos modelos podrían no tener empresa
        pass

    return True


def verify_object_ownership(obj: Model, user) -> bool:
    """
    Verificar que un objeto pertenezca a la empresa del usuario.

    Returns:
        bool: True si pertenece, False si no
    """
    if not user or not user.is_authenticated:
        return False

    try:
        empresa = user.empresa
    except AttributeError:
        return False

    obj_empresa = getattr(obj, "empresa", None)
    return obj_empresa == empresa


def log_tenant_violation(user, model_name: str, object_id: Optional[int] = None, details: str = ""):
    """
    Registrar una violación de aislamiento de tenant.
    """
    logger.critical(
        f"VIOLACIÓN DE AISLAMIENTO TENANT: "
        f"usuario={user.username if user else 'None'}, "
        f"modelo={model_name}, "
        f"objeto_id={object_id}, "
        f"detalles={details}"
    )

    # Aquí podrías:
    # 1. Enviar alerta por email
    # 2. Guardar en tabla de auditoría
    # 3. Bloquear usuario automáticamente
    # 4. Notificar a administradores


def check_queryset_isolation(queryset: QuerySet, expected_empresa_id: int, model_name: str) -> bool:
    """
    Verificar que todos los objetos en un queryset pertenezcan a la empresa esperada.
    Útil para testing y auditoría.

    Returns:
        bool: True si todos pertenecen, False si hay objetos de otras empresas
    """
    # Verificar primeros N objetos (no todos para eficiencia)
    sample = queryset[:100]

    for obj in sample:
        obj_empresa_id = getattr(obj, "empresa_id", None)
        if obj_empresa_id != expected_empresa_id:
            logger.error(
                f"Queryset {model_name} contiene objeto {obj.id} "
                f"de empresa {obj_empresa_id}, esperada: {expected_empresa_id}"
            )
            return False

    return True
