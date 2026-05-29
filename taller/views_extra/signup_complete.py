from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import activate

from taller.forms.signup_complete import SignupCompleteForm
from taller.models.empresa import Empresa
from taller.services.trial_service import can_start_trial
from taller.utils.pais_utils import get_configuracion_pais
from taller.utils.plan_catalog import (
    BILLING_MONTHLY,
    PLAN_TRIAL,
    PLAN_ENTRY,
    PLAN_GROWTH,
    PLAN_BUSINESS,
    get_months_paid,
    get_plan_price,
    normalize_billing_cycle,
    normalize_plan_code,
)


def _format_signup_price(country, plan_code, billing_cycle):
    price_data = get_plan_price(country, plan_code, billing_cycle)
    price = price_data["price"]
    if price == price.to_integral_value():
        formatted = f"{int(price):,}"
        return formatted.replace(",", ".") if country == "CL" else formatted
    return f"{price:.2f}"


def _signup_price_context():
    return {
        "CL": {
            "mensual": {
                "valor": _format_signup_price("CL", PLAN_ENTRY, BILLING_MONTHLY),
                "periodo": "mes",
            },
            "semestral": {
                "valor": _format_signup_price("CL", PLAN_GROWTH, "semestral"),
                "periodo": "año",
            },
            "anual": {
                "valor": _format_signup_price("CL", PLAN_BUSINESS, "anual"),
                "periodo": "año",
            },
        },
        "US": {
            "mensual": {
                "valor": _format_signup_price("US", PLAN_ENTRY, BILLING_MONTHLY),
                "periodo": "month",
            },
            "semestral": {
                "valor": _format_signup_price("US", PLAN_GROWTH, "semestral"),
                "periodo": "year",
            },
            "anual": {
                "valor": _format_signup_price("US", PLAN_BUSINESS, "anual"),
                "periodo": "year",
            },
        },
        "MX": {
            "mensual": {
                "valor": _format_signup_price("MX", PLAN_ENTRY, BILLING_MONTHLY),
                "periodo": "mes",
            },
            "semestral": {
                "valor": _format_signup_price("MX", PLAN_GROWTH, "semestral"),
                "periodo": "año",
            },
            "anual": {
                "valor": _format_signup_price("MX", PLAN_BUSINESS, "anual"),
                "periodo": "año",
            },
        },
    }


def signup_complete(request):
    """
    Vista de registro completa con selección de país y plan
    💰 Preparada para generar ingresos desde día 1

    🌍 DETECCIÓN DE PAÍS:
    - ?from=cl → Español, pre-selecciona Chile
    - ?from=us → Inglés, pre-selecciona USA
    - Sin parámetro → Inglés por defecto
    """
    # 🎯 DETECTAR PAÍS DESDE URL
    from_country = request.GET.get("from", "us").lower()

    # 🌐 ACTIVAR IDIOMA SEGÚN PAÍS
    if from_country == "br":
        activate("pt")  # Portugués para Brasil
        initial_country = "BR"
        language_code = "pt"
    elif from_country == "cl":
        activate("es")  # Español para Chile
        initial_country = "CL"
        language_code = "es"
    elif from_country == "mx":
        activate("es")  # Español para México
        initial_country = "MX"
        language_code = "es"
    elif from_country == "pe":
        activate("es")  # Español para Perú
        initial_country = "PE"
        language_code = "es"
    elif from_country == "ve":
        activate("es")  # Español para Venezuela
        initial_country = "VE"
        language_code = "es"
    else:
        activate("en")  # Inglés por defecto (USA)
        initial_country = "US"
        language_code = "en"

    if request.method == "POST":
        form = SignupCompleteForm(request.POST)

        if form.is_valid():
            # Extraer datos del formulario
            nombre = form.cleaned_data["nombre"]
            apellido = form.cleaned_data["apellido"]
            email = form.cleaned_data["email"]
            # Campos opcionales - usar valores por defecto si no se proporcionan
            nombre_taller = form.cleaned_data.get("nombre_taller") or f"Taller de {nombre}"
            telefono = form.cleaned_data.get("telefono") or ""
            # El país se determina desde ?from=cl o desde el formulario
            pais = form.cleaned_data.get("pais") or initial_country
            plan = normalize_plan_code(form.cleaned_data["plan"])
            billing_cycle = normalize_billing_cycle(
                form.cleaned_data.get("billing_cycle") or plan
            )
            password = form.cleaned_data["password1"]

            if plan == PLAN_TRIAL:
                trial_allowed, _trial_reason = can_start_trial(
                    type("TrialCandidate", (), {"email": email, "telefono": telefono})()
                )
                if not trial_allowed:
                    form.add_error(
                        "plan",
                        "La prueba gratis ya fue usada para estos datos. Puedes elegir Entry, Growth o Business sin tarjeta.",
                    )
                    return render(
                        request,
                        "auth/signup.html",
                        {
                            "form": form,
                            "from_country": from_country,
                            "language_code": language_code,
                            "precios": _signup_price_context(),
                        },
                    )

            try:
                with transaction.atomic():
                    # 🔥 PASO 1: CREAR USUARIO
                    user = User.objects.create_user(
                        username=email,  # Usar email como username
                        email=email,
                        password=password,
                        first_name=nombre,
                        last_name=apellido,
                        is_active=True,
                    )

                    # 🔥 PASO 2: CONFIGURACIÓN POR PLAN
                    is_trial = plan == PLAN_TRIAL
                    plan_price = get_plan_price(pais, plan, billing_cycle)
                    valor_mensual = plan_price["price"]
                    days_to_expire = 30 if billing_cycle == BILLING_MONTHLY else 365
                    meses_pagados = get_months_paid(billing_cycle)

                    pais_config = get_configuracion_pais(type("TmpEmpresa", (), {"pais": pais})())

                    # 🔥 PASO 3: CREAR EMPRESA (SUSCRIPTOR)
                    empresa = Empresa.objects.create(
                        user=user,
                        nombre_taller=nombre_taller,
                        email=email,
                        telefono=telefono,
                        # Configuración por país (auto-asignado)
                        pais=pais,
                        moneda=pais_config["moneda"],
                        zona_horaria=pais_config["zona_horaria_default"],
                        # Configuración del plan
                        plan=plan,
                        dias_prueba=30 if is_trial else 0,
                        valor_mensual=valor_mensual,
                        # Fechas
                        fecha_inicio=timezone.now(),
                        fecha_fin=timezone.now() + timedelta(days=days_to_expire),
                        # Estado de suscripción
                        suscripcion_activa=is_trial,
                    )

                    # 🔥 PASO 4: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL
                    # FORZAR verificación de email SIEMPRE (independiente de configuración)
                    account_email_verification = getattr(
                        settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory"
                    )
                    requires_email_verification = account_email_verification == "mandatory"

                    # DEBUG: Log para verificar configuración
                    print(f"🔍 DEBUG: ACCOUNT_EMAIL_VERIFICATION = {account_email_verification}")
                    print(f"🔍 DEBUG: requires_email_verification = {requires_email_verification}")

                    # FORZAR verificación SIEMPRE (comentar esta línea si quieres respetar la configuración)
                    requires_email_verification = True
                    print(f"🔍 DEBUG: FORZANDO requires_email_verification = True")

                    # 🔥 PASO 5: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN
                    if requires_email_verification:
                        # Crear EmailAddress para allauth
                        try:
                            from allauth.account.models import EmailAddress
                            from allauth.account.utils import send_email_confirmation

                            # Crear o obtener EmailAddress
                            email_address, created = EmailAddress.objects.get_or_create(
                                user=user,
                                email=email,
                                defaults={"verified": False, "primary": True},
                            )

                            # Si ya existe pero está verificado, no hacer nada
                            if not email_address.verified:
                                # Enviar email de confirmación
                                # Usar fail_silently=True para que no bloquee el registro si hay problemas de conexión
                                try:
                                    send_email_confirmation(request, user, email=email)
                                except (TimeoutError, ConnectionError) as e:
                                    # Log del error pero no bloquear el registro
                                    import logging

                                    logger = logging.getLogger(__name__)
                                    logger.warning(
                                        f"⚠️  No se pudo enviar email de confirmación debido a timeout/conexión: {e}. "
                                        "El usuario puede solicitar reenvío desde la página de confirmación."
                                    )
                        except Exception as e:
                            import logging

                            logger = logging.getLogger(__name__)
                            logger.warning(f"⚠️  Error creando EmailAddress o enviando email: {e}")
                            # No bloquear el registro si hay problemas con el email

                    # 🔥 PASO 6: SI SE REQUIERE VERIFICACIÓN, NO HACER LOGIN - REDIRIGIR A CONFIRMACIÓN
                    if requires_email_verification:
                        # NO hacer login automático - redirigir a página de confirmación
                        is_spanish = pais in {"CL", "MX", "CO", "PE", "VE", "EC"}
                        if is_spanish:
                            messages.success(
                                request,
                                "¡Cuenta creada exitosamente! Por favor, revisa tu email para activar tu cuenta.",
                            )
                        else:
                            messages.success(
                                request,
                                "Account created successfully! Please check your email to activate your account.",
                            )
                        # Redirigir a la página de confirmación de email (nueva página)
                        # Construir URL según el país
                        if pais == "CL":
                            verification_url = "/cl/es/accounts/confirm-email/"
                        elif pais == "MX":
                            verification_url = "/mx/es/accounts/confirm-email/"
                        else:
                            verification_url = "/us/en/accounts/confirm-email/"
                        return redirect(verification_url)

                    # 🔥 PASO 7: SI NO SE REQUIERE VERIFICACIÓN, HACER LOGIN AUTOMÁTICO
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )
                    # Nota: No llamar request.session.save() explícitamente
                    # Django guarda la sesión automáticamente al final de la request
                    # Hacerlo dentro de una transacción puede causar "database is locked" con SQLite

                    # 🔥 PASO 8: MENSAJE DE BIENVENIDA
                    is_spanish = pais in {"CL", "MX", "CO", "PE", "VE", "EC"}
                    if plan == "trial":
                        messages.success(
                            request,
                            (
                                f"¡Bienvenido {nombre}! Tu prueba gratuita de 30 días ha comenzado."
                                if is_spanish
                                else f"Welcome {nombre}! Your 30-day free trial has started."
                            ),
                        )
                    else:
                        messages.info(
                            request,
                            (
                                f"Cuenta creada. Completa el pago para activar tu plan {plan}."
                                if is_spanish
                                else f"Account created. Complete your payment to activate the {plan} plan."
                            ),
                        )

                    # 🔥 PASO 9: REDIRIGIR SEGÚN PAÍS Y PLAN
                    if plan == "trial":
                        # Trial: acceso inmediato al dashboard
                        if pais == "BR":
                            return redirect("/br/pt/dashboard/")
                        elif pais == "CL":
                            return redirect("/cl/es/dashboard/")
                        elif pais == "MX":
                            return redirect("/mx/es/dashboard/")
                        elif pais == "PE":
                            return redirect("/pe/es/dashboard/")
                        elif pais == "VE":
                            return redirect("/ve/es/dashboard/")
                        else:
                            return redirect("/us/centro-operaciones/")
                    else:
                        # Planes pagados: a página de pago
                        if pais == "BR":
                            return redirect(
                                f"/br/pt/suscripcion/pago/?plan={plan}&billing={billing_cycle}&amount={valor_mensual}"
                            )
                        elif pais == "CL":
                            return redirect(
                                f"/cl/es/suscripcion/pago/?plan={plan}&billing={billing_cycle}&amount={valor_mensual}"
                            )
                        elif pais == "MX":
                            return redirect(
                                f"/mx/es/suscripcion/pago/?plan={plan}&billing={billing_cycle}&amount={valor_mensual}"
                            )
                        elif pais == "PE":
                            return redirect(
                                f"/pe/es/suscripcion/pago/?plan={plan}&billing={billing_cycle}&amount={valor_mensual}"
                            )
                        elif pais == "VE":
                            return redirect(
                                f"/ve/es/suscripcion/pago/?plan={plan}&billing={billing_cycle}&amount={valor_mensual}"
                            )
                        else:
                            return redirect(
                                f"/us/en/subscription/payment/?plan={plan}&billing={billing_cycle}&amount={valor_mensual}"
                            )

            except Exception as e:
                messages.error(request, f"Error al crear cuenta: {str(e)}")
                form.add_error(None, f"Error al crear cuenta: {str(e)}")

    else:
        # 🎯 PRE-SELECCIONAR PAÍS SEGÚN URL
        form = SignupCompleteForm(initial={"pais": initial_country})

    # Precios para mostrar en el template
    context = {
        "form": form,
        "from_country": from_country,  # 'cl', 'us' o 'mx'
        "language_code": language_code,  # 'es' o 'en'
        "precios": _signup_price_context(),
    }

    return render(request, "auth/signup.html", context)
