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
    try:
        embudo, created = RegistroEmbudoSuscriptor.objects.get_or_create(
            user=user,
            defaults={
                "pais": pais,
                "fecha_registro": timezone.now(),
                "obtuvo_trial": obtuvo_trial,
                "trial_started_at": trial_started_at,
                "trial_ends_at": trial_ends_at,
            },
        )
        if created:
            log.info(f"[Embudo] Signup registrado para {user.email} ({pais})")
        else:
            log.warning(f"[Embudo] Embudo ya existía para {user.email}")
    except Exception as e:
        log.error(f"[Embudo] Error registrando signup para {user.email}: {e}", exc_info=True)


def registrar_email_confirmado(user):
    """
    Registra la confirmación de email en el embudo.

    Args:
        user: Usuario que confirmó el email
    """
    try:
        embudo = RegistroEmbudoSuscriptor.objects.filter(user=user).first()
        if embudo and not embudo.email_confirmado_at:
            embudo.email_confirmado_at = timezone.now()
            embudo.save(update_fields=["email_confirmado_at"])
            log.info(f"[Embudo] Email confirmado para {user.email}")
        elif not embudo:
            log.warning(f"[Embudo] No se encontró embudo para {user.email} al confirmar email")
    except Exception as e:
        log.error(
            f"[Embudo] Error registrando email confirmado para {user.email}: {e}", exc_info=True
        )


def registrar_primer_login(user):
    """
    Registra el primer login en el embudo.

    Args:
        user: Usuario que hizo login
    """
    try:
        embudo = RegistroEmbudoSuscriptor.objects.filter(user=user).first()
        if embudo and not embudo.primer_login_at:
            embudo.primer_login_at = timezone.now()
            embudo.save(update_fields=["primer_login_at"])
            log.info(f"[Embudo] Primer login registrado para {user.email}")
        elif not embudo:
            log.warning(f"[Embudo] No se encontró embudo para {user.email} al hacer login")
    except Exception as e:
        log.error(f"[Embudo] Error registrando primer login para {user.email}: {e}", exc_info=True)


def registrar_empresa_creada(user):
    """
    Registra la creación de empresa en el embudo.

    Args:
        user: Usuario para el que se creó la empresa
    """
    try:
        embudo = RegistroEmbudoSuscriptor.objects.filter(user=user).first()
        if embudo and not embudo.empresa_creada_at:
            embudo.empresa_creada_at = timezone.now()
            embudo.save(update_fields=["empresa_creada_at"])
            log.info(f"[Embudo] Empresa creada registrada para {user.email}")
        elif not embudo:
            log.warning(f"[Embudo] No se encontró embudo para {user.email} al crear empresa")
    except Exception as e:
        log.error(
            f"[Embudo] Error registrando empresa creada para {user.email}: {e}", exc_info=True
        )
