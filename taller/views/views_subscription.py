from django.core.mail import send_mail
from django.shortcuts import render
from django.conf import settings
from .forms_subscription import PlanPagoForm

def registro_plan_pago(request):
    if request.method == 'POST':
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
            return render(request, "registro_enviado.html", {"tipo": "plan"})
    else:
        form = PlanPagoForm()
    return render(request, "registro.html", {"form": form})
