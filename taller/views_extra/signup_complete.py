from datetime import timedelta
from decimal import Decimal

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
from taller.utils.pais_utils import get_configuracion_pais


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
            plan = form.cleaned_data["plan"]
            password = form.cleaned_data["password1"]

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
                    plan_config = {
                        "trial": {
                            "dias": 30,
                            "valores": {
                                "BR": Decimal("0.00"),
                                "CL": Decimal("0.00"),
                                "MX": Decimal("0.00"),
                                "PE": Decimal("0.00"),
                                "US": Decimal("0.00"),
                                "VE": Decimal("0.00"),
                            },
                            "suscripcion_activa": True,  # Trial activo inmediatamente
                            "plan_nombre": "trial",
                        },
                        "mensual": {
                            "dias": 30,
                            "valores": {
                                "BR": Decimal("100.00"),  # R$ 100 BRL
                                "CL": Decimal("10000.00"),  # $10,000 CLP
                                "MX": Decimal("399.00"),  # $399 MXN
                                "PE": Decimal("70.00"),  # S/ 70 PEN
                                "US": Decimal("20.00"),  # $20 USD
                                "VE": Decimal("730.00"),  # Bs. 730 VES
                            },
                            "suscripcion_activa": False,  # Debe pagar primero
                            "plan_nombre": "basic",
                        },
                        "semestral": {
                            "dias": 180,
                            "valores": {
                                "BR": Decimal("500.00"),  # R$ 500 BRL
                                "CL": Decimal("55000.00"),  # $55,000 CLP
                                "MX": Decimal("2199.00"),  # $2,199 MXN
                                "PE": Decimal("350.00"),  # S/ 350 PEN
                                "US": Decimal("110.00"),  # $110 USD
                                "VE": Decimal("3650.00"),  # Bs. 3,650 VES
                            },
                            "suscripcion_activa": False,
                            "plan_nombre": "premium",
                        },
                        "anual": {
                            "dias": 365,
                            "valores": {
                                "BR": Decimal("1000.00"),  # R$ 1,000 BRL
                                "CL": Decimal("100000.00"),  # $100,000 CLP
                                "MX": Decimal("3990.00"),  # $3,990 MXN
                                "PE": Decimal("700.00"),  # S/ 700 PEN
                                "US": Decimal("200.00"),  # $200 USD
                                "VE": Decimal("7300.00"),  # Bs. 7,300 VES
                            },
                            "suscripcion_activa": False,
                            "plan_nombre": "enterprise",
                        },
                    }

                    config = plan_config[plan]

                    # Determinar valor según país
                    valores_por_pais = config["valores"]
                    valor_mensual = valores_por_pais.get(pais, valores_por_pais.get("CL"))

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
                        plan=config["plan_nombre"],
                        dias_prueba=config["dias"],
                        valor_mensual=valor_mensual,
                        # Fechas
                        fecha_inicio=timezone.now(),
                        fecha_fin=timezone.now() + timedelta(days=config["dias"]),
                        # Estado de suscripción
                        suscripcion_activa=config["suscripcion_activa"],
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
                                f"/br/pt/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        elif pais == "CL":
                            return redirect(
                                f"/cl/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        elif pais == "MX":
                            return redirect(
                                f"/mx/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        elif pais == "PE":
                            return redirect(
                                f"/pe/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        elif pais == "VE":
                            return redirect(
                                f"/ve/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        else:
                            return redirect(
                                f"/us/en/subscription/payment/?plan={plan}&amount={valor_mensual}"
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
        "precios": {
            "CL": {
                "mensual": {"valor": "10.000", "periodo": "mes"},
                "semestral": {"valor": "55.000", "periodo": "6 meses", "ahorro": "8%"},
                "anual": {"valor": "100.000", "periodo": "año", "ahorro": "17%"},
            },
            "US": {
                "mensual": {"valor": "20", "periodo": "month"},
                "semestral": {"valor": "110", "periodo": "6 months", "ahorro": "8%"},
                "anual": {"valor": "200", "periodo": "year", "ahorro": "17%"},
            },
            "MX": {
                "mensual": {"valor": "399", "periodo": "mes"},
                "semestral": {"valor": "2,199", "periodo": "6 meses", "ahorro": "8%"},
                "anual": {"valor": "3,990", "periodo": "año", "ahorro": "17%"},
            },
        },
    }

    return render(request, "auth/signup.html", context)
