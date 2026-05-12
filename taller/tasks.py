from django.conf import settings
from django.utils import timezone

from .models.suscripcion import Suscripcion
from .utils.email_helper import get_branded_from_email, send_email_with_reply_to


def verificar_suscripciones():
    hoy = timezone.now().date()
    for sus in Suscripcion.objects.filter(activa=True):
        if sus.esta_por_expirar():
            send_email_with_reply_to(
                subject="Tu suscripción está por expirar",
                message=(
                    f"Tu plan finaliza el {sus.fecha_expiracion}. "
                    "Renueva ahora para evitar interrupciones."
                ),
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=[sus.usuario.email],
            )
        if sus.expiro():
            sus.activa = False
            sus.save()
            send_email_with_reply_to(
                subject="Tu suscripción ha expirado",
                message=(
                    "Tu acceso ha sido desactivado. Para renovarlo, "
                    "realiza el pago y envía el comprobante."
                ),
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=[sus.usuario.email],
            )
