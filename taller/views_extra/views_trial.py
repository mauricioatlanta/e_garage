import re

from django.conf import settings
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_protect

from taller.utils.email_helper import (
    get_branded_from_email,
    get_support_reply_to,
    send_email_with_reply_to,
)


@csrf_protect
def registro_trial(request):
    # Import movido aquí para evitar AppRegistryNotReady
    from taller.models.trial import TrialRegistro

    mensaje = error = None
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip().lower()
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.headers.get("user-agent", "")

        if not nombre or not email:
            error = "Todos los campos son obligatorios."
        elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
            error = "Correo electrónico no válido."
        elif TrialRegistro.objects.filter(email=email).exists():
            error = "Ya existe una prueba activa o registrada para este correo."
        else:
            codigo = get_random_string(12)
            TrialRegistro.objects.create(
                nombre=nombre, email=email, codigo=codigo, ip=ip, user_agent=user_agent
            )
            try:
                destinatarios = [email, get_support_reply_to()]
                link_activacion = f"https://egarage.cl/cl/es/activar-trial/?email={email}"
                cuerpo = (
                    f"Hola {nombre},\n\n"
                    f"Tu código de instalación seguro es: {codigo}\n\n"
                    "Para activar tu cuenta, haz clic en el siguiente enlace e ingresa "
                    f"tu código de activación:\n{link_activacion}\n\n"
                    "Gracias por probar eGarage.\n"
                )
                send_email_with_reply_to(
                    subject="Tu código de instalación de eGarage",
                    message=cuerpo,
                    from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                    recipient_list=destinatarios,
                    fail_silently=False,
                )
                mensaje = "¡Código enviado! Revisa tu correo electrónico."
            except Exception:
                error = "No se pudo enviar el correo. Intenta nuevamente."

    return render(request, "registro_trial.html", {"mensaje": mensaje, "error": error})
