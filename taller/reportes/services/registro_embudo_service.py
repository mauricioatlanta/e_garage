"""
Servicio para actualizar el embudo de registro de suscriptores
"""

import logging
from django.utils import timezone

from taller.models.registro_embudo import RegistroEmbudoSuscriptor

log = logging.getLogger(__name__)


def registrar_signup(user, pais, obtuvo_trial=False, trial_started_at=None, trial_ends_at=None):
    """
    Registra el signup en el embudo.

    Args:
        user: Usuario que se registró
        pais: Código de país (CL, US, MX, etc.)
        obtuvo_trial: Si obtuvo trial de 30 días
        trial_started_at: Fecha de inicio del trial (opcional)
        trial_ends_at: Fecha de fin del trial (opcional)
    """
    from taller.services.registro_embudo_service import registrar_signup as canonical

    return canonical(user, pais, obtuvo_trial, trial_started_at, trial_ends_at)


def registrar_email_confirmado(user):
    """
    Registra la confirmación de email en el embudo.

    Args:
        user: Usuario que confirmó el email
    """
    from taller.services.registro_embudo_service import registrar_email_confirmado as canonical

    return canonical(user)


def registrar_primer_login(user, request=None):
    """
    Registra el primer login en el embudo.

    Args:
        user: Usuario que hizo login
    """
    from taller.services.registro_embudo_service import registrar_primer_login as canonical

    return canonical(user, request=request)


def registrar_empresa_creada(user):
    """
    Registra la creación de empresa en el embudo.

    Args:
        user: Usuario para el que se creó la empresa
    """
    from taller.services.registro_embudo_service import registrar_empresa_creada as canonical

    return canonical(user)
