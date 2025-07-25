
from django.core.mail import send_mail
from django.conf import settings
from .forms_trial import TrialForm
from .forms_subscription import PlanPagoForm
from taller.models.trial import TrialRegistro
from django.utils.crypto import get_random_string
import re
from django.shortcuts import render

def registro_unificado(request):
    mensaje = error = None
    tipo = request.POST.get('tipo_registro', 'trial')
    form = None
    if request.method == 'POST':
        if tipo == 'trial':
            form = TrialForm(request.POST)
            if form.is_valid():
                nombre = form.cleaned_data['nombre']
                email = form.cleaned_data['email']
                telefono = form.cleaned_data['telefono']
                codigo = get_random_string(12)
                TrialRegistro.objects.create(
                    nombre=nombre,
                    email=email,
                    telefono=telefono,
                    codigo=codigo,
                    ip=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                destinatarios = [email, 'suscripcion@atlantareciclajes.cl']
                send_mail(
                    'Tu código de instalación de E-Garage',
                    f'Hola {nombre},\n\nTu código de instalación seguro es: {codigo}\n\nGracias por probar E-Garage.\n',
                    settings.DEFAULT_FROM_EMAIL,
                    destinatarios,
                    fail_silently=False,
                )
                mensaje = '¡Código enviado! Revisa tu correo electrónico.'
                return render(request, 'registro_enviado.html', {'mensaje': mensaje, 'tipo': 'trial'})
        elif tipo == 'pago':
            form = PlanPagoForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                send_mail(
                    subject='Gracias por suscribirte a eGarage',
                    message=(
                        "Bienvenido a eGarage. Para activar tu plan, realiza la transferencia a:\n\n"
                        "Banco: Banco Ejemplo\n"
                        "Cuenta: 123456789\n"
                        "Rut: 11.111.111-1\n"
                        "Correo para enviar voucher: suscripcion@atlantareciclajes.cl\n\n"
                        "Una vez validado el pago, activaremos tu cuenta."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                mensaje = '¡Gracias por tu interés! Te enviamos los datos bancarios.'
                return render(request, 'registro_enviado.html', {'mensaje': mensaje, 'tipo': 'plan'})
    if not form:
        form = TrialForm() if tipo == 'trial' else PlanPagoForm()
    return render(request, 'registro.html', {'form': form, 'tipo': tipo})
