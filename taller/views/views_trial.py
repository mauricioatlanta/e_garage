from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from taller.models.trial import TrialRegistro
import re

@csrf_protect
def registro_trial(request):
    mensaje = error = None
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip().lower()
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        # Validación básica
        if not nombre or not email:
            error = 'Todos los campos son obligatorios.'
        elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
            error = 'Correo electrónico no válido.'
        elif TrialRegistro.objects.filter(email=email).exists():
            error = 'Ya existe una prueba activa o registrada para este correo.'
        else:
            # Generar código seguro
            codigo = get_random_string(12)
            # Guardar registro
            TrialRegistro.objects.create(
                nombre=nombre,
                email=email,
                codigo=codigo,
                ip=ip,
                user_agent=user_agent
            )
            # Enviar email seguro
            try:
                # Enviar al usuario y a subcripcion@atlantareciclajes.cl
                destinatarios = [email, 'subcripcion@atlantareciclajes.cl']
                link_activacion = f'https://tusitio.com/activar-trial/?email={email}'
                mensaje = (
                    f'Hola {nombre},\n\n'
                    f'Tu código de instalación seguro es: {codigo}\n\n'
                    f'Para activar tu cuenta, haz clic en el siguiente enlace e ingresa tu código de activación:\n{link_activacion}\n\n'
                    'Gracias por probar E-Garage.\n'
                )
                send_mail(
                    'Tu código de instalación de E-Garage',
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    destinatarios,
                    fail_silently=False,
                )
                mensaje = '¡Código enviado! Revisa tu correo electrónico.'
            except Exception as e:
                error = 'No se pudo enviar el correo. Intenta nuevamente.'
    return render(request, 'registro_trial.html', {'mensaje': mensaje, 'error': error})
