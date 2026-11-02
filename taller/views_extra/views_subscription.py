from django.conf import settings
from django.shortcuts import render

from taller.utils.email_helper import (
    get_branded_from_email,
    get_support_reply_to,
    send_email_with_reply_to,
)
from taller.utils.payment_config import build_transfer_payment_message

from taller.forms_subscription import PlanPagoForm


def registro_plan_pago(request):
    # Obtenemos la empresa de forma segura si el usuario está autenticado
    empresa_actual = getattr(request.user, "empresa", None) if request.user.is_authenticated else None

    if request.method == "POST":
        # Pasamos la empresa actual al formulario para validar los cupos en el clean()
        form = PlanPagoForm(request.POST, empresa_actual=empresa_actual)
        if form.is_valid():
            # Usamos un valor por defecto seguro en caso de que el formulario no contenga el campo email
            email = form.cleaned_data.get("email", getattr(request.user, "email", ""))
            
            if email:
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
        form = PlanPagoForm(empresa_actual=empresa_actual)
        
    return render(request, "registro.html", {"form": form})


from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib import messages
from taller.services.data_exporter_service import DataExporterService

@login_required
def cancelar_suscripcion_view(request):
    """
    Endpoint para dar de baja el taller. Cambia los estados de la empresa,
    asigna la fecha de baja para la purga de 6 meses y despacha el correo maestro.
    """
    empresa = getattr(request.user, 'empresa', None)
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asociada.')
        return redirect('taller:dashboard')

    if request.method == 'POST':
        # 1. Aplicar la baja y encender el cronómetro de 6 meses
        empresa.suscripcion_activa = False
        empresa.fecha_baja = timezone.now()
        empresa.save()

        # 2. Despachar el JSON masivo a su bandeja de entrada
        DataExporterService.exportar_y_enviar_datos(empresa)

        # 3. Informar y cerrar sesión del usuario de forma segura
        from django.contrib.auth import logout
        logout(request)
        messages.success(request, 'Tu suscripción ha sido cancelada. Enviamos un respaldo con tus datos a tu email corporativo.')
        return render(request, 'bloqueada.html', {'tipo': 'cancelado'})

    return render(request, 'saas/suscripcion/confirmar_cancelacion.html', {'empresa': empresa})
