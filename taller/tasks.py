from django.core.mail import send_mail
from .models.suscripcion import Suscripcion
from django.utils import timezone
from django.conf import settings

def verificar_suscripciones():
    hoy = timezone.now().date()
    for sus in Suscripcion.objects.filter(activa=True):
        if sus.esta_por_expirar():
            send_mail(
                'Tu suscripción está por expirar',
                f'Tu plan finaliza el {sus.fecha_expiracion}. Renueva ahora para evitar interrupciones.',
                settings.DEFAULT_FROM_EMAIL,
                [sus.usuario.email]
            )
        if sus.expiro():
            sus.activa = False
            sus.save()
            send_mail(
                'Tu suscripción ha expirado',
                f'Tu acceso ha sido desactivado. Para renovarlo, realiza el pago y envía el comprobante.',
                settings.DEFAULT_FROM_EMAIL,
                [sus.usuario.email]
            )
