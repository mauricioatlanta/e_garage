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


from django.shortcuts import render

from taller.auth.country_login_required import country_login_required


@country_login_required
def dashboard(request):
    """
    Dashboard principal. Chile: Home Operativo Mobile (Menú 1).
    USA/otros: redirige al Centro de Operaciones correspondiente.
    """
    from django.shortcuts import redirect
    from django.template.response import TemplateResponse
    from django.utils import timezone
    from django.utils.translation import get_language

    path = request.path
    if path.startswith("/cl/"):
        # Chile: render Home Operativo Mobile (no redirección)
        return _dashboard_home_operativo_chile(request)
    elif path.startswith("/us/"):
        return redirect("usa:centro_operaciones_espacial")
    else:
        return redirect("taller:centro_operaciones")


def _dashboard_home_operativo_chile(request):
    """Vista Home Operativo Mobile para Chile: KPIs y misiones del día."""
    from datetime import date
    from decimal import Decimal

    from django.contrib import messages
    from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
    from django.db.models.functions import Coalesce
    from django.shortcuts import redirect
    from django.template import TemplateDoesNotExist
    from django.template.loader import get_template
    from django.template.response import TemplateResponse
    from django.utils.translation import get_language

    from taller.models.documento import Documento
    from taller.models.lineas_documento import LineaRepuesto, LineaServicio
    from taller.utils.templates import select_country_lang_template

    try:
        empresa = request.user.empresa
    except Exception:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        return redirect("chile:configuracion")

    hoy = timezone.localdate()
    inicio_mes = date(hoy.year, hoy.month, 1)
    zero_dec = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))
    subtotal_expr = ExpressionWrapper(
        F("precio_unitario") * F("cantidad"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    # Ventas mes (facturación FAC del mes: servicios + repuestos)
    base_mes_srv = LineaServicio.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=inicio_mes,
        documento__tipo="FAC",
    )
    base_mes_rep = LineaRepuesto.objects.filter(
        documento__empresa=empresa,
        documento__fecha_emision__gte=inicio_mes,
        documento__tipo="FAC",
    )
    ventas_mes = (
        base_mes_srv.aggregate(t=Coalesce(Sum(subtotal_expr), zero_dec))["t"]
        + base_mes_rep.aggregate(t=Coalesce(Sum(subtotal_expr), zero_dec))["t"]
    ) or Decimal("0")

    # IVA mes (CL: 19% sobre repuestos)
    total_rep_mes = base_mes_rep.aggregate(t=Coalesce(Sum(subtotal_expr), zero_dec))[
        "t"
    ] or Decimal("0")
    iva_mes = (
        (total_rep_mes * Decimal("0.19")).quantize(Decimal("0.01"))
        if empresa.pais == "CL"
        else Decimal("0")
    )

    # Pendientes hoy: presupuestos abiertos (simplificado)
    pendientes_hoy = Documento.objects.filter(empresa=empresa, tipo="PRES").count()
    ot_en_progreso = Documento.objects.filter(empresa=empresa, tipo="OT").count()
    # Por cobrar: facturas del mes (como indicador; sin estado de cobro real)
    por_cobrar = Documento.objects.filter(
        empresa=empresa, tipo="FAC", fecha_emision__gte=inicio_mes
    ).count()

    # Misiones del día: listas simples para el template
    ot_list = (
        Documento.objects.filter(empresa=empresa, tipo="OT")
        .select_related("cliente", "vehiculo")
        .order_by("-fecha_emision")[:10]
    )
    pres_list = (
        Documento.objects.filter(empresa=empresa, tipo="PRES")
        .select_related("cliente", "vehiculo")
        .order_by("-fecha_emision")[:10]
    )

    from django.urls import reverse

    context = {
        "empresa": empresa,
        "ventas_mes": ventas_mes,
        "iva_mes": iva_mes,
        "pendientes_hoy": pendientes_hoy,
        "ot_en_progreso": ot_en_progreso,
        "por_cobrar": por_cobrar,
        "moneda": getattr(empresa, "simbolo_moneda", "$"),
        "ot_list": ot_list,
        "pres_list": pres_list,
        "fecha_hoy": hoy,
        "nav_url_dashboard": reverse("chile:dashboard"),
        "nav_url_documentos": reverse("chile:lista_documentos_cl"),
        "nav_url_ai_lab": reverse("chile:ai_lab"),
        "nav_url_centro_operaciones": reverse("chile:centro_operaciones"),
        "nav_url_crear_documento": reverse("chile:crear_documento_cl"),
    }

    # Override Chile: cl/es/dashboard/home_operativo.html; fallback común
    if getattr(empresa, "pais", "").upper() == "CL":
        try:
            get_template("cl/es/dashboard/home_operativo.html")
            template_name = "cl/es/dashboard/home_operativo.html"
        except TemplateDoesNotExist:
            template_name = "taller/common/dashboard/home_operativo_mobile.html"
    else:
        template_name = select_country_lang_template(
            "dashboard/home_operativo_mobile.html",
            getattr(empresa, "pais", "cl").lower(),
            get_language(),
        )
        try:
            get_template(template_name)
        except TemplateDoesNotExist:
            template_name = "taller/common/dashboard/home_operativo_mobile.html"

    return TemplateResponse(request, template_name, context)


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
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

from taller.forms_subscription import PlanPagoForm
from taller.forms_trial import TrialForm
from taller.models.trial import TrialRegistro


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
