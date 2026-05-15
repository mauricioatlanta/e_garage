from django.conf import settings
from django.shortcuts import render

from taller.utils.email_helper import (
    get_branded_from_email,
    get_support_reply_to,
    send_email_with_reply_to,
)
from taller.utils.payment_config import build_transfer_payment_message

from .forms_subscription import PlanPagoForm


def registro_plan_pago(request):
    if request.method == "POST":
        form = PlanPagoForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            send_email_with_reply_to(
                subject="Gracias por suscribirte a eGarage",
                message=(
                    "Bienvenido a eGarage. Para activar tu plan, realiza la transferencia a:\n\n"
                    f"{build_transfer_payment_message('CL')}\n\n"
                    "Una vez validado el pago, activaremos tu cuenta."
                ),
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=[email],
                fail_silently=False,
            )
            return render(request, "registro_enviado.html", {"tipo": "plan"})
    else:
        form = PlanPagoForm()
    return render(request, "registro.html", {"form": form})
