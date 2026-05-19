from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from taller.forms.comprobante_form import ComprobantePagoForm
from taller.models.comprobante_pago import ComprobantePago
from taller.models.empresa import Empresa
from taller.utils.payment_config import get_transfer_payment_details
from taller.utils.empresa import get_or_create_empresa
from taller.utils.plan_catalog import (
    BILLING_ANNUAL,
    BILLING_MONTHLY,
    PLAN_BUSINESS,
    PLAN_ENTRY,
    PLAN_GROWTH,
    PLAN_TRIAL,
    get_plan_price,
    get_supported_payment_methods,
)


def suspension(request):
    """Vista de suspensión por suscripción vencida"""
    if not request.user.is_authenticated:
        return redirect("account_login")

    try:
        from taller.utils.empresa import get_user_empresa_safe

        empresa = get_user_empresa_safe(request.user)
        if not empresa:
            messages.error(request, "No se encontró información de empresa")
            return redirect("taller:dashboard")
    except Exception:
        messages.error(request, "No se encontró información de empresa")
        return redirect("taller:dashboard")

    # Si la suscripción está activa, redirigir al dashboard
    if not empresa.debe_bloquear:
        return redirect("taller:dashboard")

    # Obtener comprobantes pendientes
    comprobantes_pendientes = ComprobantePago.objects.filter(
        empresa=empresa, estado="pendiente"
    ).order_by("-fecha_subida")

    # Días transcurridos desde vencimiento (evita mostrar valores negativos en UI)
    dias_transcurridos_suspension = 0
    try:
        if empresa.fecha_expiracion:
            dias_transcurridos_suspension = max(0, (timezone.now() - empresa.fecha_expiracion).days)
    except Exception:
        dias_transcurridos_suspension = 0

    context = {
        "empresa": empresa,
        "comprobantes_pendientes": comprobantes_pendientes,
        "dias_transcurridos_suspension": dias_transcurridos_suspension,
        "whatsapp_url": (
            "https://wa.me/"
            f"{getattr(settings, 'SUPPORT_WHATSAPP_WA_ME', '56953574683')}"
            f"?text=Hola, necesito renovar mi suscripcion de eGarage para {empresa.nombre_taller}"
        ),
        "datos_transferencia": get_transfer_payment_details(empresa.pais),
        "precios": {
            "basic": get_plan_price(empresa.pais, "basic", "mensual")["price"],
            "premium": get_plan_price(empresa.pais, "premium", "semestral")["price"],
            "enterprise": get_plan_price(empresa.pais, "enterprise", "anual")["price"],
        },
    }

    return render(request, "suspension/suspension.html", context)


@login_required
def subir_comprobante(request):
    """Vista para subir comprobante de pago"""
    try:
        from taller.utils.empresa import get_user_empresa_safe

        empresa = get_user_empresa_safe(request.user)
        if not empresa:
            messages.error(request, "No se encontró información de empresa")
            return redirect("taller:dashboard")
    except Exception:
        messages.error(request, "No se encontró información de empresa")
        return redirect("taller:dashboard")

    if request.method == "POST":
        form = ComprobantePagoForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.empresa = empresa
            comprobante.save()

            messages.success(
                request,
                "Comprobante subido exitosamente. Te notificaremos cuando sea revisado.",
            )
            return redirect("suspension")
    else:
        form = ComprobantePagoForm()

    context = {
        "form": form,
        "empresa": empresa,
    }

    return render(request, "suspension/subir_comprobante.html", context)


@login_required
def estado_suscripcion(request):
    """Vista AJAX para obtener estado de suscripción"""
    try:
        empresa = request.user.empresa
        data = {
            "dias_restantes": empresa.dias_restantes,
            "fecha_expiracion": empresa.fecha_expiracion.strftime("%d/%m/%Y"),
            "estado": empresa.estado_suscripcion,
            "debe_mostrar_alerta": empresa.debe_mostrar_alerta(),
            "mensaje_alerta": empresa.get_mensaje_alerta(),
            "color_estado": empresa.color_estado,
        }
        return JsonResponse(data)
    except Empresa.DoesNotExist:
        return JsonResponse({"error": "Empresa no encontrada"}, status=404)


@login_required
def registrar_transferencia_ajax(request):
    """Registra un comprobante de transferencia bancaria para revisión manual."""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    empresa = get_or_create_empresa(request)

    post_data = request.POST.copy()
    post_data["metodo_pago"] = "transferencia"
    post_data["plan_solicitado"] = empresa.plan or "basic"
    if request.POST.get("referencia") and not post_data.get("numero_transaccion"):
        post_data["numero_transaccion"] = request.POST.get("referencia")
    if request.POST.get("notas") and not post_data.get("descripcion"):
        post_data["descripcion"] = request.POST.get("notas")

    files_data = request.FILES.copy()
    if "archivo" in files_data and "comprobante" not in files_data:
        files_data.setlist("comprobante", files_data.getlist("archivo"))

    form = ComprobantePagoForm(post_data, files_data)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    comprobante = form.save(commit=False)
    comprobante.empresa = empresa
    comprobante.estado = "pendiente"

    renewal_period = (
        request.POST.get("renewal_period") or request.POST.get("periodo") or "mensual"
    ).strip().lower()
    annual_keys = {"anual", "annual", "12", "yearly", "year"}
    comprobante.meses_pagados = 12 if renewal_period in annual_keys else 1

    # El comprobante se guarda en estado pendiente y no extiende la suscripción aún.
    comprobante.save()

    return JsonResponse(
        {
            "success": True,
            "message": "Comprobante recibido. Estamos validando la transferencia.",
            "comprobante_id": comprobante.id,
        }
    )


def precios(request):
    """Vista pública con información de precios diferenciada por país"""
    from taller.models.precio_suscripcion import PrecioSuscripcion

    def format_clp(value):
        """Formato CLP: $20.000 (sin decimales)."""
        try:
            return f"${int(float(value)):,}".replace(",", ".")
        except (TypeError, ValueError):
            return "$0"

    def format_catalog_price(country, plan, billing):
        price_data = get_plan_price(country, plan, billing)
        amount = price_data["price"]
        currency = price_data["currency"]
        if currency == "CLP":
            return f"{format_clp(amount)} CLP"
        if currency == "MXN":
            return f"${amount:,.0f} MXN"
        return f"USD {amount:,.0f}"

    def build_pricing_cards(country):
        methods = ", ".join(get_supported_payment_methods(country)).replace("_", " ")
        signup_paths = {
            "AR": "/ar/es/accounts/signup/",
            "BR": "/br/es/accounts/signup/",
            "CL": "/cl/es/accounts/signup/",
            "CO": "/co/es/accounts/signup/",
            "EC": "/ec/es/accounts/signup/",
            "MX": "/mx/es/accounts/signup/",
            "PE": "/pe/es/accounts/signup/",
            "US": "/us/signup/",
            "UY": "/uy/es/accounts/signup/",
            "VE": "/ve/es/accounts/signup/",
        }
        signup_path = signup_paths.get(country, "/accounts/signup/")
        return [
            {
                "plan": PLAN_TRIAL,
                "pricing": "$0",
                "billing_cycle": BILLING_MONTHLY,
                "payment_methods": "Sin tarjeta",
                "highlight": False,
                "cta_url": f"{signup_path}?plan=trial",
            },
            {
                "plan": PLAN_ENTRY,
                "pricing": (
                    f"{format_catalog_price(country, PLAN_ENTRY, BILLING_MONTHLY)} mensual / "
                    f"{format_catalog_price(country, PLAN_ENTRY, BILLING_ANNUAL)} anual"
                ),
                "billing_cycle": BILLING_MONTHLY,
                "payment_methods": methods,
                "highlight": False,
                "cta_url": f"{signup_path}?plan={PLAN_ENTRY}",
            },
            {
                "plan": PLAN_GROWTH,
                "pricing": (
                    f"{format_catalog_price(country, PLAN_GROWTH, BILLING_MONTHLY)} mensual / "
                    f"{format_catalog_price(country, PLAN_GROWTH, BILLING_ANNUAL)} anual"
                ),
                "billing_cycle": BILLING_MONTHLY,
                "payment_methods": methods,
                "highlight": True,
                "cta_url": f"{signup_path}?plan={PLAN_GROWTH}",
            },
            {
                "plan": PLAN_BUSINESS,
                "pricing": (
                    f"{format_catalog_price(country, PLAN_BUSINESS, BILLING_MONTHLY)} mensual / "
                    f"{format_catalog_price(country, PLAN_BUSINESS, BILLING_ANNUAL)} anual"
                ),
                "billing_cycle": BILLING_MONTHLY,
                "payment_methods": methods,
                "highlight": False,
                "cta_url": f"{signup_path}?plan={PLAN_BUSINESS}",
            },
        ]

    # Detectar país del usuario desde la URL o empresa
    pais_usuario = "US"  # Default USA para la ruta /us/pricing/

    # Detectar desde la ruta
    if request.path.startswith("/us/"):
        pais_usuario = "US"
    elif request.path.startswith("/cl/"):
        pais_usuario = "CL"
    elif request.path.startswith("/br/"):
        pais_usuario = "BR"
    elif request.path.startswith("/ve/"):
        pais_usuario = "VE"
    elif request.path.startswith("/pe/"):
        pais_usuario = "PE"
    elif request.path.startswith("/mx/"):
        pais_usuario = "MX"
    elif request.path.startswith("/co/"):
        pais_usuario = "CO"
    elif request.path.startswith("/ec/"):
        pais_usuario = "EC"
    # Override si el usuario está autenticado
    elif request.user.is_authenticated and hasattr(request.user, "empresa"):
        pais_usuario = request.user.empresa.pais
    elif request.GET.get("country"):
        pais_usuario = request.GET.get("country").upper()

    # Obtener precios según el país usando el nuevo manager
    planes_precios = PrecioSuscripcion.objects.activos().para_pais(pais_usuario).order_by("precio")

    # Si no hay precios configurados, usar valores por defecto
    if not planes_precios.exists():
        # Crear estructura de precios por defecto
        if pais_usuario == "US":
            # Precios USA en dólares
            # Características diferenciadas por plan

            planes = {
                "mensual": {
                    "nombre": "Monthly Plan USA",
                    "nombre_en": "Monthly Plan USA",
                    "nombre_es": "Plan Mensual USA",
                    "precio": get_plan_price("US", "entry", "mensual")["price"],
                    "moneda": get_plan_price("US", "entry", "mensual")["currency"],
                    "caracteristicas": [
                        "Unlimited documents",
                        "Up to 5 users",
                        "Priority support",
                        "24/7 Premium support",
                    ],
                    "caracteristicas_en": [
                        "Unlimited documents",
                        "Up to 5 users",
                        "Priority support",
                        "24/7 Premium support",
                    ],
                    "caracteristicas_es": [
                        "Documentos ilimitados",
                        "Hasta 5 usuarios",
                        "Soporte prioritario",
                        "Soporte 24/7 Premium",
                    ],
                },
                "semestral": {
                    "nombre": "Semi-Annual Plan USA",
                    "nombre_en": "Semi-Annual Plan USA",
                    "nombre_es": "Plan Semestral USA",
                    "precio": get_plan_price("US", "growth", "semestral")["price"],
                    "moneda": get_plan_price("US", "growth", "semestral")["currency"],
                    "caracteristicas": [
                        "Unlimited documents",
                        "Up to 8 users",
                        "Advanced reports",
                        "AI diagnostics included",
                        "Priority support",
                        "24/7 Premium support",
                    ],
                    "caracteristicas_en": [
                        "Unlimited documents",
                        "Up to 8 users",
                        "Advanced reports",
                        "AI diagnostics included",
                        "Priority support",
                        "24/7 Premium support",
                    ],
                    "caracteristicas_es": [
                        "Documentos ilimitados",
                        "Hasta 8 usuarios",
                        "Reportes avanzados",
                        "Diagnóstico IA incluido",
                        "Soporte prioritario",
                        "Soporte 24/7 Premium",
                    ],
                },
                "anual": {
                    "nombre": "Annual Plan USA",
                    "nombre_en": "Annual Plan USA",
                    "nombre_es": "Plan Anual USA",
                    "precio": get_plan_price("US", "business", "anual")["price"],
                    "moneda": get_plan_price("US", "business", "anual")["currency"],
                    "caracteristicas": [
                        "Unlimited documents",
                        "Unlimited users",
                        "Advanced reports",
                        "AI diagnostics included",
                        "Priority support",
                        "Custom API",
                        "Multi-location support",
                        "24/7 Premium support",
                    ],
                    "caracteristicas_en": [
                        "Unlimited documents",
                        "Unlimited users",
                        "Advanced reports",
                        "AI diagnostics included",
                        "Priority support",
                        "Custom API",
                        "Multi-location support",
                        "24/7 Premium support",
                    ],
                    "caracteristicas_es": [
                        "Documentos ilimitados",
                        "Usuarios ilimitados",
                        "Reportes avanzados",
                        "Diagnóstico IA incluido",
                        "Soporte prioritario",
                        "API personalizada",
                        "Multi-sucursales",
                        "Soporte 24/7 Premium",
                    ],
                },
            }
            # Formato USA: $1,250.25 (coma miles, 2 decimales)
            for p in planes.values():
                p["precio_formateado"] = f"${p['precio']:,.2f}"
        elif pais_usuario == "BR":
            # Precios Brasil en reales
            caracteristicas_brasil = [
                "Ordens ilimitadas",
                "Usuários ilimitados",
                "Relatórios avançados",
                "Diagnóstico IA incluído",
                "Suporte prioritário",
                "API personalizada",
                "Multi-filiais",
                "Suporte 24/7 Premium",
            ]

            planes = {
                "mensual": {
                    "nombre": "Plano Mensal",
                    "precio": 100,
                    "moneda": "BRL",
                    "caracteristicas": caracteristicas_brasil,
                },
                "semestral": {
                    "nombre": "Plano Semestral",
                    "precio": 500,
                    "moneda": "BRL",
                    "caracteristicas": caracteristicas_brasil,
                    "ahorro": "17%",
                },
                "anual": {
                    "nombre": "Plano Anual",
                    "precio": 1000,
                    "moneda": "BRL",
                    "caracteristicas": caracteristicas_brasil,
                    "ahorro": "33%",
                },
            }
        elif pais_usuario == "VE":
            # Precios Venezuela en bolívares
            caracteristicas_venezuela = [
                "Órdenes ilimitadas",
                "Usuarios ilimitados",
                "Reportes avanzados",
                "Diagnóstico IA incluido",
                "Soporte prioritario",
                "API personalizada",
                "Multi-sucursales",
                "Soporte 24/7 Premium",
            ]

            planes = {
                "mensual": {
                    "nombre": "Plan Mensual",
                    "precio": 730,
                    "moneda": "VES",
                    "caracteristicas": caracteristicas_venezuela,
                },
                "semestral": {
                    "nombre": "Plan Semestral",
                    "precio": 3650,
                    "moneda": "VES",
                    "caracteristicas": caracteristicas_venezuela,
                    "ahorro": "17%",
                },
                "anual": {
                    "nombre": "Plan Anual",
                    "precio": 7300,
                    "moneda": "VES",
                    "caracteristicas": caracteristicas_venezuela,
                    "ahorro": "33%",
                },
            }
        elif pais_usuario == "PE":
            # Precios Perú en soles
            caracteristicas_peru = [
                "Órdenes ilimitadas",
                "Usuarios ilimitados",
                "Reportes avanzados",
                "Diagnóstico IA incluido",
                "Soporte prioritario",
                "API personalizada",
                "Multi-sucursales",
                "Soporte 24/7 Premium",
            ]

            planes = {
                "mensual": {
                    "nombre": "Plan Mensual",
                    "precio": 70,
                    "moneda": "PEN",
                    "caracteristicas": caracteristicas_peru,
                },
                "semestral": {
                    "nombre": "Plan Semestral",
                    "precio": 350,
                    "moneda": "PEN",
                    "caracteristicas": caracteristicas_peru,
                    "ahorro": "17%",
                },
                "anual": {
                    "nombre": "Plan Anual",
                    "precio": 700,
                    "moneda": "PEN",
                    "caracteristicas": caracteristicas_peru,
                    "ahorro": "33%",
                },
            }
        elif pais_usuario == "MX":
            planes = {
                "prueba": {
                    "nombre": "Prueba 30 días",
                    "precio": 0,
                    "moneda": "MXN",
                    "caracteristicas": [
                        "Acceso completo por 30 días",
                        "Soporte de onboarding y migración básica",
                        "Plantillas de órdenes, compras y facturas CFDI",
                    ],
                },
                "mensual": {
                    "nombre": "Operación Mensual",
                    "precio": 360,
                    "moneda": "MXN",
                    "caracteristicas": [
                        "Usuarios ilimitados y roles por área",
                        "Inventario, compras y cotizaciones sincronizadas",
                        "Dashboards de productividad y ventas",
                    ],
                },
                "cinco_meses": {
                    "nombre": "Plan 5 Meses",
                    "precio": 1800,
                    "moneda": "MXN",
                    "caracteristicas": [
                        "Vigencia continua de 5 meses",
                        "Capacitación remota para equipos de piso y mostrador",
                        "Reportes comparativos por sucursal o línea de negocio",
                    ],
                },
                "anual": {
                    "nombre": "Plan Anual",
                    "precio": 3600,
                    "moneda": "MXN",
                    "caracteristicas": [
                        "Vigencia anual con soporte priority extendido",
                        "Auditoría trimestral de procesos e inventario",
                        "Planes de crecimiento para nuevas sedes y servicios",
                    ],
                },
            }
        else:
            # Precios Chile en pesos
            # Características IGUALES para todos los planes
            caracteristicas_chile = [
                "Documentos ilimitados",
                "Usuarios ilimitados",
                "Reportes avanzados",
                "Diagnóstico IA incluido",
                "Soporte prioritario",
                "API personalizada",
                "Multi-sucursales",
                "Soporte 24/7 Premium",
            ]

            planes = {
                "prueba": {
                    "nombre": "Prueba 30 días",
                    "nombre_en": "30-Day Free Trial",
                    "nombre_es": "Prueba 30 días",
                    "precio": 0,
                    "moneda": "CLP",
                    "precio_formateado": format_clp(0),
                    "caracteristicas": [
                        "Acceso completo a todos los módulos por 30 días",
                        "Sin tarjeta de crédito",
                        "Soporte de onboarding inicial",
                    ],
                    "caracteristicas_en": [
                        "Full access to all modules for 30 days",
                        "No credit card required",
                        "Initial onboarding support",
                    ],
                    "caracteristicas_es": [
                        "Acceso completo a todos los módulos por 30 días",
                        "Sin tarjeta de crédito",
                        "Soporte de onboarding inicial",
                    ],
                },
                "mensual": {
                    "nombre": "Plan Mensual",
                    "precio": 20000,
                    "moneda": "CLP",
                    "precio_formateado": format_clp(20000),
                    "caracteristicas": caracteristicas_chile,
                },
                "semestral": {
                    "nombre": "Plan Semestral",
                    "precio": 100000,
                    "moneda": "CLP",
                    "precio_formateado": format_clp(100000),
                    "caracteristicas": caracteristicas_chile,
                },
                "anual": {
                    "nombre": "Plan Anual",
                    "precio": 200000,
                    "moneda": "CLP",
                    "precio_formateado": format_clp(200000),
                    "caracteristicas": caracteristicas_chile,
                },
            }
    else:
        # Usar precios de la base de datos
        # Determinar idioma según país
        lang = "en" if pais_usuario == "US" else "es"

        planes = {}
        for precio in planes_precios:
            # Traducir nombres de planes si es USA
            nombre_plan = precio.nombre_plan
            if pais_usuario == "US":
                # Traducir nombres al inglés y agregar "USA"
                if "mensual" in precio.tipo_plan.lower():
                    nombre_plan = "Monthly Plan USA"
                elif "semestral" in precio.tipo_plan.lower():
                    nombre_plan = "Semi-Annual Plan USA"
                elif "anual" in precio.tipo_plan.lower():
                    nombre_plan = "Annual Plan USA"

            planes[precio.tipo_plan] = {
                "nombre": nombre_plan,
                "nombre_en": nombre_plan,
                "nombre_es": nombre_plan,
                "precio": precio.precio,
                "moneda": precio.moneda,
                "caracteristicas": precio.caracteristicas_list(lang=lang),
                "caracteristicas_en": precio.caracteristicas_list(lang="en"),
                "caracteristicas_es": precio.caracteristicas_list(lang="es"),
                "precio_formateado": (
                    format_clp(precio.precio)
                    if pais_usuario == "CL"
                    else precio.precio_formateado()
                ),
            }

        # Chile: asegurar plan gratis aunque la grilla venga de BD.
        if pais_usuario == "CL" and "prueba" not in planes:
            planes = {
                "prueba": {
                    "nombre": "Prueba 30 días",
                    "nombre_en": "30-Day Free Trial",
                    "nombre_es": "Prueba 30 días",
                    "precio": 0,
                    "moneda": "CLP",
                    "precio_formateado": format_clp(0),
                    "caracteristicas": [
                        "Acceso completo a todos los módulos por 30 días",
                        "Sin tarjeta de crédito",
                        "Soporte de onboarding inicial",
                    ],
                    "caracteristicas_en": [
                        "Full access to all modules for 30 days",
                        "No credit card required",
                        "Initial onboarding support",
                    ],
                    "caracteristicas_es": [
                        "Acceso completo a todos los módulos por 30 días",
                        "Sin tarjeta de crédito",
                        "Soporte de onboarding inicial",
                    ],
                },
                **planes,
            }

    # Información de contacto según el país
    whatsapp_contacto = (
        "https://wa.me/56912345678?text=Hola, quiero información sobre los planes de eGarage"
    )
    if pais_usuario == "US":
        whatsapp_contacto = (
            "https://wa.me/15551234567?text=Hi, I want information about eGarage plans"
        )
    elif pais_usuario == "BR":
        whatsapp_contacto = (
            "https://wa.me/5511999999999?text=Olá, quero informação sobre os planos do eGarage"
        )
    elif pais_usuario == "VE":
        whatsapp_contacto = (
            "https://wa.me/584121234567?text=Hola, quiero información sobre los planes de eGarage"
        )
    elif pais_usuario == "PE":
        whatsapp_contacto = (
            "https://wa.me/51987654321?text=Hola, quiero información sobre los planes de eGarage"
        )
    elif pais_usuario == "MX":
        whatsapp_contacto = "https://wa.me/525512345678?text=Hola, quiero información sobre los planes de eGarage México"

    # Símbolos de moneda por país
    simbolos_moneda = {
        "US": "$",
        "CL": "$",
        "BR": "R$",
        "VE": "Bs.",
        "PE": "S/",
        "MX": "$",
    }

    context = {
        "planes": planes,
        "pricing_cards": build_pricing_cards(pais_usuario),
        "pais_usuario": pais_usuario,
        "whatsapp_contacto": whatsapp_contacto,
        "moneda_simbolo": simbolos_moneda.get(pais_usuario, "$"),
        "es_chile": pais_usuario == "CL",
        "es_usa": pais_usuario == "US",
        "es_brasil": pais_usuario == "BR",
        "es_venezuela": pais_usuario == "VE",
        "es_peru": pais_usuario == "PE",
        "es_mexico": pais_usuario == "MX",
    }

    return render(request, "suspension/precios.html", context)
