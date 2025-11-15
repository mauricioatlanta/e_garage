from datetime import timedelta
from decimal import Decimal

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
    if from_country == "cl":
        activate("es")  # Español para Chile
        initial_country = "CL"
        language_code = "es"
    elif from_country == "mx":
        activate("es")  # Español para México
        initial_country = "MX"
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
            nombre_taller = form.cleaned_data["nombre_taller"]
            telefono = form.cleaned_data["telefono"]
            pais = form.cleaned_data["pais"]
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
                                "CL": Decimal("0.00"),
                                "US": Decimal("0.00"),
                                "MX": Decimal("0.00"),
                            },
                            "suscripcion_activa": True,  # Trial activo inmediatamente
                            "plan_nombre": "trial",
                        },
                        "mensual": {
                            "dias": 30,
                            "valores": {
                                "CL": Decimal("10000.00"),  # $10,000 CLP
                                "US": Decimal("20.00"),  # $20 USD
                                "MX": Decimal("399.00"),  # $399 MXN
                            },
                            "suscripcion_activa": False,  # Debe pagar primero
                            "plan_nombre": "basic",
                        },
                        "semestral": {
                            "dias": 180,
                            "valores": {
                                "CL": Decimal("55000.00"),  # $55,000 CLP
                                "US": Decimal("110.00"),  # $110 USD
                                "MX": Decimal("2199.00"),  # $2,199 MXN
                            },
                            "suscripcion_activa": False,
                            "plan_nombre": "premium",
                        },
                        "anual": {
                            "dias": 365,
                            "valores": {
                                "CL": Decimal("100000.00"),  # $100,000 CLP
                                "US": Decimal("200.00"),  # $200 USD
                                "MX": Decimal("3990.00"),  # $3,990 MXN
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

                    # 🔥 PASO 4: LOGIN AUTOMÁTICO
                    # Especificar backend para evitar errores de sesión
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )

                    # Forzar guardado de la nueva sesión para evitar SessionInterrupted
                    request.session.save()

                    # 🔥 PASO 5: MENSAJE DE BIENVENIDA
                    is_spanish = pais in {"CL", "MX"}
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

                    # 🔥 PASO 6: REDIRIGIR SEGÚN PAÍS Y PLAN
                    if plan == "trial":
                        # Trial: acceso inmediato al dashboard
                        if pais == "CL":
                            return redirect("/cl/es/dashboard/")
                        elif pais == "MX":
                            return redirect("/mx/es/dashboard/")
                        else:
                            return redirect("/us/en/dashboard/")
                    else:
                        # Planes pagados: a página de pago
                        if pais == "CL":
                            return redirect(
                                f"/cl/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        elif pais == "MX":
                            return redirect(
                                f"/mx/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
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
