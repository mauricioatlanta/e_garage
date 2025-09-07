from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def enviar_email_reset_manual(request):
    user = get_user_model().objects.filter(email="mauricioatlanta@gmail.com").first()
    if not user:
        return HttpResponse("Usuario de prueba no existe.")

    context = {
        "email": user.email,
        "domain": "127.0.0.1:8000",
        "site_name": "eGarage",
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "user": user,
        "token": default_token_generator.make_token(user),
        "protocol": "http",
    }

    subject = render_to_string("registration/password_reset_subject.txt").strip()
    body = render_to_string("registration/password_reset_email.html", context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email="eGarage <no-responder@egarage.com>",
        to=[user.email],
    )
    email.attach_alternative(body, "text/html")  # Enviar como HTML
    email.send()
    return HttpResponse("Correo enviado manualmente (HTML)")


from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from taller.models.documento import Documento
from taller.models.repuesto import Repuesto
from taller.models.venta import Venta


@login_required
def dashboard(request):
    """
    Dashboard principal - Redirige al Centro de Operaciones empresarial
    para una mejor experiencia del usuario
    """
    # Redirigir automáticamente al nuevo dashboard empresarial
    from django.shortcuts import redirect

    return redirect("taller:centro_operaciones")


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

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


import re

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render
from django.utils.crypto import get_random_string

from taller.forms_subscription import PlanPagoForm
from taller.forms_trial import TrialForm
from taller.models.trial import TrialRegistro


def registro_unificado(request):
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
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )
                destinatarios = [email, "suscripcion@atlantareciclajes.cl"]
                send_mail(
                    "Tu código de instalación de E-Garage",
                    f"Hola {nombre},\n\nTu código de instalación seguro es: {codigo}\n\nGracias por probar E-Garage.\n",
                    settings.DEFAULT_FROM_EMAIL,
                    destinatarios,
                    fail_silently=False,
                )
                mensaje = "¡Código enviado! Revisa tu correo electrónico."
                return render(
                    request,
                    "registro_enviado.html",
                    {"mensaje": mensaje, "tipo": "trial"},
                )
        elif tipo == "pago":
            form = PlanPagoForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data["email"]
                send_mail(
                    subject="Gracias por suscribirte a eGarage",
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
                mensaje = "¡Gracias por tu interés! Te enviamos los datos bancarios."
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
from django.shortcuts import redirect, render


@login_required
def suscripcion_bloqueada(request):
    logout(request)
    return render(request, "bloqueada.html")


from django.shortcuts import render


def debug_cliente_autocomplete(request):
    return render(request, "debug_autocomplete_cliente.html")


# --- Vistas de administración de suscripciones ---

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion


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
            empresa = request.user.empresa
            suscripciones = Suscripcion.objects.filter(
                empresa=empresa
            )  # 🔒 FILTRO EMPRESA
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
