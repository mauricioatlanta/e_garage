from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    """
    Dashboard principal - Redirige al Centro de Operaciones empresarial
    para una mejor experiencia del usuario
    """
    # Redirigir automáticamente al nuevo dashboard empresarial
    from django.shortcuts import redirect

    # Detectar país desde la URL para usar el namespace correcto
    path = request.path
    if path.startswith("/cl/"):
        # Chile - usar namespace chile
        return redirect("chile:centro_operaciones")
    elif path.startswith("/us/"):
        # USA - usar namespace usa
        return redirect("usa:centro_operaciones_espacial")
    else:
        # Fallback - usar namespace taller
        return redirect("taller:centro_operaciones")


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from taller.empresa_forms import EmpresaForm
from taller.models.empresa import Empresa


@login_required
def editar_empresa(request):
    empresa, created = Empresa.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            return redirect("taller:dashboard")  # o donde desees
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, "empresa_form.html", {"form": form})


from django.conf import settings
from django.utils.crypto import get_random_string

from taller.forms_subscription import PlanPagoForm
from taller.forms_trial import TrialForm
from taller.models.trial import TrialRegistro
from taller.utils.email_helper import (
    get_branded_from_email,
    get_support_reply_to,
    send_email_with_reply_to,
)
from taller.utils.payment_config import build_transfer_payment_message


def registro_unificado_legacy(request):
    """
    ⚠️ DEPRECATED: Esta función ha sido reemplazada por el sistema unificado.

    Redirige al flujo moderno de registro.
    """
    from django.http import HttpResponsePermanentRedirect

    return HttpResponsePermanentRedirect("/registro/")
    mensaje = error = None
    tipo = request.POST.get("tipo_registro", "trial")
    form = None
    if request.method == "POST":
        if tipo == "trial":
            form = TrialForm(request.POST)
            if form.is_valid():
                nombre = form.cleaned_data["nombre"]
                email = form.cleaned_data["email"]
                telefono = form.cleaned_data["telefono"]
                codigo = get_random_string(12)
                TrialRegistro.objects.create(
                    nombre=nombre,
                    email=email,
                    telefono=telefono,
                    codigo=codigo,
                    ip=request.META.get("REMOTE_ADDR"),
                    user_agent=request.headers.get("user-agent", ""),
                )
                destinatarios = [email, get_support_reply_to()]
                send_email_with_reply_to(
                    subject="Tu codigo de instalacion de eGarage",
                    message=(
                        f"Hola {nombre},\n\n"
                        f"Tu codigo de instalacion seguro es: {codigo}\n\n"
                        "Gracias por probar eGarage.\n"
                    ),
                    from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                    recipient_list=destinatarios,
                    fail_silently=False,
                )
                mensaje = "Codigo enviado. Revisa tu correo electronico."
                return render(
                    request,
                    "registro_enviado.html",
                    {"mensaje": mensaje, "tipo": "trial"},
                )
        elif tipo == "pago":
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
                mensaje = "Gracias por tu interes. Te enviamos los datos bancarios."
                return render(
                    request,
                    "registro_enviado.html",
                    {"mensaje": mensaje, "tipo": "plan"},
                )
    if not form:
        form = TrialForm() if tipo == "trial" else PlanPagoForm()
    return render(request, "registro.html", {"form": form, "tipo": tipo})


from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


@login_required
def suscripcion_bloqueada(request):
    logout(request)
    return render(request, "bloqueada.html")


def debug_cliente_autocomplete(request):
    return render(request, "debug_autocomplete_cliente.html")


# --- Vistas de administración de suscripciones ---

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from taller.models.suscripcion import Suscripcion
from taller.services.empresa_service import get_empresa_safe


# Vista protegida con métricas de suscripciones
@login_required
@user_passes_test(lambda u: u.is_staff)
def dashboard_suscripciones(request):
    # Para staff: mostrar todas las suscripciones (función administrativa)
    # Para usuarios normales: solo de su empresa
    if request.user.is_staff:
        suscripciones = Suscripcion.objects.all()  # Admin ve todas
    else:
        # Usuario normal solo ve suscripciones relacionadas con su empresa
        try:
            empresa = get_empresa_safe(request)
            if not empresa:
                suscripciones = Suscripcion.objects.none()
            else:
                suscripciones = Suscripcion.objects.filter(empresa=empresa)  # 🔒 FILTRO EMPRESA
        except:
            suscripciones = Suscripcion.objects.none()

    activas = sum(1 for s in suscripciones if s.activa and not s.esta_vencida())
    por_vencer = sum(1 for s in suscripciones if s.activa and s.por_vencer())
    vencidas = sum(1 for s in suscripciones if s.esta_vencida())
    return render(
        request,
        "dashboard.htm",
        {
            "activas": activas,
            "por_vencer": por_vencer,
            "vencidas": vencidas,
        },
    )


@user_passes_test(lambda u: u.is_staff)
def renovar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == "POST":
        empresa.fecha_inicio = now()
        empresa.suscripcion_activa = True
        empresa.save()
    return redirect("dashboard_suscripciones")


def landing_egarage(request):
    """Vista para servir la landing page de eGarage"""
    return render(request, "landing_egarage.html")
