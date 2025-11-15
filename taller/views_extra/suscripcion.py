from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from taller.models.taller_info import TallerInfo
from taller.models.trial import TrialRegistro

from ..forms.suscripcion import FormularioRegistro
from ..models.empresa import Empresa


@login_required
def suscripcion_bloqueada(request):
    return render(
        request,
        "suscripcion_bloqueada.html",
        {"dias_restantes": 0, "empresa": getattr(request, "empresa", None)},
    )


def _activation_url(request, pais: str) -> str:
    # Construye URL con dominio real
    if pais == "US":
        path = "/us/activar-trial/"
    elif pais == "MX":
        path = "/mx/es/activar-trial/"
    else:
        path = "/cl/es/activar-trial/"
    return request.build_absolute_uri(path)


def _normaliza_email(email: str) -> str:
    return (email or "").strip().lower()


def registro(request):
    if request.method == "POST":
        form = FormularioRegistro(request.POST, request=request)
        tipo_registro = request.POST.get("tipo_registro")
        if not form.is_valid():
            return render(request, "suscripcion/registro.html", {"form": form})

        User = get_user_model()

        email = _normaliza_email(form.cleaned_data["email"])
        telefono = form.cleaned_data["telefono"]
        nombre_taller = form.cleaned_data["nombre_taller"]
        plan = form.cleaned_data["plan"]
        pais = form.cleaned_data["pais"]

        # Evita duplicados por email
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user and Empresa.objects.filter(user=existing_user).exists():
            return render(request, "suscripcion/usuario_existente.html", {"email": email})

        # Validar prueba gratuita (si corresponde)
        if tipo_registro == "trial":
            from taller.views_extra.registro_utils import validar_prueba

            if not validar_prueba(email, telefono):
                return render(
                    request,
                    "suscripcion/prueba_ya_usada.html",
                    {"email": email, "telefono": telefono},
                )

        with transaction.atomic():
            user = form.save()  # asume que el form setea email normalizado
            # Seguridad: si ya tiene empresa, corta flujo
            if Empresa.objects.filter(user=user).exists():
                messages.warning(request, "Ya tienes una empresa asociada.")
                return redirect("taller:dashboard")  # ajusta a tu vista real

            empresa = Empresa.objects.create(
                user=user, nombre_taller=nombre_taller, email=email, pais=pais
            )
            TallerInfo.objects.create(
                user=user,
                nombre_taller=nombre_taller,
                telefono=telefono,
                ha_usado_prueba=(tipo_registro == "trial"),
            )

            if tipo_registro == "trial":
                # Generar y persistir código con expiración (ej. 24h)
                import random

                codigo = f"{random.randint(100000, 999999)}"
                TrialRegistro.objects.create(
                    nombre=user.first_name or user.username,
                    email=email,
                    telefono=telefono,
                    codigo=codigo,
                    ip=request.META.get("REMOTE_ADDR"),
                    user_agent=request.headers.get("user-agent", ""),
                    creado_en=timezone.now(),
                    expira_en=timezone.now() + timezone.timedelta(hours=24),
                    user=user,
                )

                activation_url = _activation_url(request, pais)
                send_mail(
                    "Código de activación eGarage - Prueba Gratuita",
                    (
                        f"Hola {user.first_name or user.username},\n\n"
                        f"Tu código de activación es: {codigo}\n"
                        f"Válido por 24 horas.\n\n"
                        f"Activa tu cuenta aquí: {activation_url}\n\n"
                        f"Ingresa tu email ({email}) y el código.\n\n"
                        f"¡Bienvenido a eGarage!"
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
                # Guarda referencia en sesión para UX más fluida (opcional)
                request.session["usuario_activacion"] = user.username
                return render(request, "registro_enviado.html", {"codigo": True})

            # Suscripción pagada
            montos = getattr(
                settings,
                "EGARAGE_PLAN_AMOUNTS",
                {
                    "mensual": {"US": "$20.00 USD", "CL": "$20.000 CLP", "MX": "$399 MXN"},
                    "semestral": {"US": "$110.00 USD", "CL": "$110.000 CLP", "MX": "$2,199 MXN"},
                    "anual": {"US": "$200.00 USD", "CL": "$200.000 CLP", "MX": "$3,990 MXN"},
                },
            )
            monto = montos.get(plan, {}).get(pais, "Consultar precio")

            cuentas = getattr(
                settings,
                "EGARAGE_BANK_ACCOUNTS",
                {
                    "US": "Cuenta bancaria USA - [configurar]",
                    "CL": "Cuenta bancaria Chile - [configurar]",
                    "MX": "Cuenta bancaria México - [configurar]",
                },
            )
            cuenta_bancaria = cuentas.get(pais, "[configurar]")

            soporte_email = getattr(settings, "EGARAGE_SUPPORT_EMAIL", "subscription@egarage.cl")

            send_mail(
                "Instrucciones de Pago - eGarage",
                (
                    f"Hola {user.first_name or user.username},\n\n"
                    f"Gracias por registrarte en eGarage (plan: {plan}).\n\n"
                    f"➡ Monto: {monto}\n"
                    f"➡ Cuenta bancaria: {cuenta_bancaria}\n"
                    f"➡ Concepto: eGarage - {user.username} - {plan}\n\n"
                    f"Después del pago:\n"
                    f"1) Envía el comprobante a: {soporte_email}\n"
                    f"2) Espera confirmación (24-48h hábiles)\n\n"
                    f"¡Gracias por elegir eGarage!"
                ),
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
            return render(
                request,
                "registro_enviado.html",
                {"pago": True, "plan": plan, "monto": monto},
            )

    # GET
    form = FormularioRegistro(request=request)
    return render(request, "suscripcion/registro.html", {"form": form})


def activar(request):
    User = get_user_model()
    username = request.session.get("usuario_activacion")
    if request.method == "GET":
        # Si no hay sesión, igual muestra el form de activación
        return render(request, "suscripcion/activar_codigo.html", {"prefill_username": username})

    # POST
    email = _normaliza_email(request.POST.get("email"))
    codigo_ingresado = (request.POST.get("codigo") or "").strip()

    # Buscar código válido en BD
    tr = (
        TrialRegistro.objects.filter(
            email__iexact=email,
            codigo=codigo_ingresado,
            expira_en__gte=timezone.now(),
        )
        .order_by("-creado_en")
        .first()
    )

    if not tr:
        messages.error(request, "Código inválido o expirado.")
        return render(request, "error_activacion.html")

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(request, "Usuario no encontrado para ese email.")
        return render(request, "error_activacion.html")

    # Activar suscripción trial (ajusta a tu modelo real)
    suscripcion = getattr(user, "suscripcion", None)
    if not suscripcion:
        messages.error(request, "La suscripción no existe aún para este usuario.")
        return render(request, "error_activacion.html")

    with transaction.atomic():
        suscripcion.activar()  # tu método real
        # Invalida el código usado
        TrialRegistro.objects.filter(pk=tr.pk).update(expira_en=timezone.now())

    # Limpia sesión opcionalmente
    request.session.pop("usuario_activacion", None)
    return render(request, "activado.html")
