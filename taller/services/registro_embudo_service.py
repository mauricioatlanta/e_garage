"""
Servicio para actualizar el embudo de registro de suscriptores
"""

import logging
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from taller.models.registro_embudo import RegistroEmbudoSuscriptor

log = logging.getLogger(__name__)


def registrar_signup(
    user,
    pais,
    obtuvo_trial=False,
    trial_started_at=None,
    trial_ends_at=None,
    request=None,
):
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
        # La empresa puede haberse creado ANTES que el registro del embudo.
        # Sincronizar la etapa empresa de forma idempotente.
        try:
            empresa = getattr(user, "empresa", None)
        except Exception:
            empresa = None

        if empresa is not None and not embudo.empresa_creada_at:
            # El flujo actual crea Empresa milisegundos antes de crear el
            # RegistroEmbudoSuscriptor. Para el funnel, una etapa posterior
            # nunca debe quedar cronológicamente antes del signup.
            empresa_fecha = getattr(empresa, "fecha_inicio", None)
            if empresa_fecha:
                embudo.empresa_creada_at = max(
                    embudo.fecha_registro,
                    empresa_fecha,
                )
            else:
                embudo.empresa_creada_at = max(
                    embudo.fecha_registro,
                    timezone.now(),
                )

            embudo.save(
                update_fields=["empresa_creada_at", "updated_at"]
            )

        if request is not None and embudo.public_session_id is None:
            try:
                from taller.services.public_analytics import get_or_create_public_session

                public_session = get_or_create_public_session(request, page_type="signup")
                embudo.public_session = public_session
                embudo.save(update_fields=["public_session", "updated_at"])
            except Exception:
                log.exception("[Embudo] Error enlazando sesión pública al signup")

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


def _allow_first_login_analytics(request, user):
    if request is None:
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return False
    if request.COOKIES.get("eg_internal_traffic"):
        return False
    domain = (getattr(settings, "PUBLIC_ANALYTICS_QA_EMAIL_DOMAIN", "") or "").strip().lower().lstrip("@")
    email = (getattr(user, "email", "") or "").strip().lower()
    return not (domain and email.endswith("@" + domain))


def registrar_primer_login(user, request=None):
    """
    Registra el primer login en el embudo.

    Args:
        user: Usuario que hizo login
    """
    try:
        with transaction.atomic():
            embudo = (
                RegistroEmbudoSuscriptor.objects.select_for_update()
                .filter(user=user)
                .first()
            )
            first_login_recorded = bool(embudo and not embudo.primer_login_at)
            if first_login_recorded:
                embudo.primer_login_at = timezone.now()
                embudo.save(update_fields=["primer_login_at", "updated_at"])
        if first_login_recorded:
            log.info(f"[Embudo] Primer login registrado para {user.email}")
            if _allow_first_login_analytics(request, user):
                try:
                    from taller.models.public_page_view import PublicAnalyticsEvent
                    from taller.services.public_analytics import create_public_event

                    create_public_event(
                        request,
                        PublicAnalyticsEvent.EVENT_FIRST_LOGIN,
                        metadata={"source": "user_logged_in"},
                    )
                except Exception:
                    log.exception("[Embudo] Error registrando first_login en analytics")
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
            try:
                from taller.models.public_page_view import PublicAnalyticsEvent
                from taller.services.public_analytics import track_model_event

                track_model_event(
                    event_type=PublicAnalyticsEvent.EVENT_COMPANY_CREATED,
                    empresa=getattr(user, "empresa", None),
                    metadata={"source": "registration_service"},
                )
            except Exception:
                log.exception("[Embudo] Error registrando company_created en analytics")
        elif not embudo:
            log.warning(f"[Embudo] No se encontró embudo para {user.email} al crear empresa")
    except Exception as e:
        log.error(
            f"[Embudo] Error registrando empresa creada para {user.email}: {e}", exc_info=True
        )
