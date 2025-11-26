import json

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import activate
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from taller.config.country_settings import CountrySettings
from taller.services.registration_service import RegistrationService
from taller.utils.country_config import get_country_config


@csrf_exempt  # Habilitar si recibes POST desde landing pages externas
@require_http_methods(["GET", "POST"])
def registro_gratuito(request):
    """
    API Endpoint para registro rápido/gratuito.

    ✅ REFACTORIZADO: Usa RegistrationService unificado con country_config.
    - Soporte para 8 países automático (CL, US, MX, PE, CO, EC, BR, VE)
    - Configuración de moneda e impuestos automática según país
    - Login automático después del registro
    - Transacciones atómicas (sin usuarios huérfanos)
    - Soporte API JSON (POST) y Template (GET)
    """
    # Manejar cambio de idioma
    lang = request.GET.get("lang")
    if lang in ["es", "en", "pt-br"]:
        activate(lang)

    if request.method == "POST":
        try:
            # 1. Parsear Datos JSON
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

            # 2. Validaciones de entrada básicas
            email = data.get("email", "").strip().lower()
            password = data.get("password")
            nombre_taller = data.get("nombre_taller", "").strip()
            nombre_usuario = data.get("nombre_usuario", email.split("@")[0] if email else "Usuario")

            if not all([email, password, nombre_taller]):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Faltan campos obligatorios (email, password, nombre_taller)",
                    },
                    status=400,
                )

            # 3. Detectar configuración de país
            # Prioridad: 1. Payload JSON, 2. URL Prefix (si existe middleware), 3. Default CL
            country_code = (
                data.get("country")
                or CountrySettings.get_country_from_url(request.path)
                or getattr(request, "country_code", None)
                or "CL"
            )
            country_code = country_code.upper()

            # ✅ Usar country_config para obtener configuración completa
            config = get_country_config(country_code)

            # 4. ⚡ USAR SERVICIO UNIFICADO
            # Esto garantiza que el usuario gratuito tenga la moneda e impuestos correctos
            try:
                result = RegistrationService.register_new_client(
                    user_data={
                        "email": email,
                        "password": password,
                        "first_name": nombre_usuario,
                        "username": email,  # Usar email como username
                    },
                    company_data={
                        "nombre_taller": nombre_taller,
                        "telefono": data.get("telefono", ""),
                    },
                    plan_type="gratuito",  # Plan gratuito ilimitado
                    country=country_code,
                    skip_email_verification=True,  # ✅ Acceso inmediato (sin código)
                    assign_role="Owner",
                    request=request,
                )

                user = result["user"]
                empresa = result["empresa"]

                # 5. Login Automático (Opcional, pero recomendado para UX)
                # Permite redirigir al usuario directo al dashboard sin pedir login de nuevo
                user = authenticate(username=email, password=password)
                if user:
                    login(request, user, backend="django.contrib.auth.backends.ModelBackend")

                # 6. Construir URL de redirección según país
                dashboard_url = (
                    CountrySettings.build_url(country_code, "dashboard/", request=request)
                    or f"/{country_code.lower()}/dashboard/"
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": f'Cuenta creada exitosamente en {config.get("name", country_code)}',
                        "redirect_url": dashboard_url,  # Redirección inteligente
                        "user_id": user.id,
                        "empresa_id": empresa.id,
                        "country": country_code,
                        "currency": config["currency"],  # Moneda asignada
                    },
                    status=201,
                )

            except ValueError as e:
                # Captura errores de validación del servicio (ej. "El email ya existe")
                return JsonResponse({"success": False, "error": str(e)}, status=400)

        except Exception as e:
            # Loguear error real en servidor
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"[RegistroGratuito] Error crítico: {e}", exc_info=True)
            return JsonResponse(
                {"success": False, "error": "Error interno del servidor"}, status=500
            )

    # GET: Renderizar template según país
    # Determinar país usando CountrySettings (sin hardcoding)
    country_code = CountrySettings.get_country_from_url(request.path) or "CL"

    # ✅ Usar country_config para obtener configuración completa
    country_config = get_country_config(country_code)

    # Configurar idioma según país
    lang = country_config.get("lang", "es")
    activate(lang)

    # Template según país e idioma
    # Soporte para 8 países con templates específicos o fallback
    template_map = {
        "US": "taller/us/en/onboarding/registro_gratuito.html",
        "CL": "taller/cl/es/onboarding/registro_gratuito.html",
        "MX": "taller/cl/es/onboarding/registro_gratuito.html",  # Usar template de CL como fallback
        "PE": "taller/cl/es/onboarding/registro_gratuito.html",
        "CO": "taller/cl/es/onboarding/registro_gratuito.html",
        "EC": "taller/cl/es/onboarding/registro_gratuito.html",
        "BR": "taller/cl/es/onboarding/registro_gratuito.html",  # TODO: Crear template en portugués
        "VE": "taller/cl/es/onboarding/registro_gratuito.html",
    }

    template = template_map.get(country_code, "taller/cl/es/onboarding/registro_gratuito.html")

    return render(
        request,
        template,
        {
            "country_config": country_config,
            "country_code": country_code,
        },
    )


def bienvenida_onboarding(request):
    """Pantalla de bienvenida con primeros pasos"""
    if not request.user.is_authenticated:
        return redirect("registro_gratuito")

    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except:
        empresa = None

    context = {"empresa": empresa, "usuario": request.user, "primer_ingreso": True}

    return render(request, "onboarding/bienvenida.html", context)


def onboarding_paso(request):
    """Pasos del onboarding interactivo"""
    if not request.user.is_authenticated:
        return redirect("onboarding:registro_gratuito")

    # Obtener paso del GET parameter, default 1
    paso = int(request.GET.get("paso", 1))

    pasos = {
        1: {
            "titulo": "👥 Agregar tu primer cliente",
            "descripcion": "Comienza agregando información de un cliente",
            "accion_url": "/clientes/nuevo/",
            "template": "onboarding/paso_cliente.html",
        },
        2: {
            "titulo": "🚗 Registrar un vehículo",
            "descripcion": "Asocia un vehículo al cliente que acabas de crear",
            "accion_url": "/vehiculos/nuevo/",
            "template": "onboarding/paso_vehiculo.html",
        },
        3: {
            "titulo": "📋 Crear tu primer documento",
            "descripcion": "Genera una cotización o factura",
            "accion_url": "/documentos/nuevo/",
            "template": "onboarding/paso_documento.html",
        },
        4: {
            "titulo": "📊 Ver reportes en acción",
            "descripcion": "Explora el poder de los reportes con IA",
            "accion_url": "/reportes/demo/",
            "template": "onboarding/paso_reportes.html",
        },
        5: {
            "titulo": "🧠 Descubre la IA integrada",
            "descripcion": "Sugerencias automáticas para tu taller",
            "accion_url": "/ia/sugerencias/",
            "template": "onboarding/paso_ia.html",
        },
        6: {
            "titulo": "🚀 SEO + Analytics configurado",
            "descripcion": "Tu taller visible en Google con métricas",
            "accion_url": "/seo/configuracion/",
            "template": "onboarding/paso_seo.html",
        },
        7: {
            "titulo": "💬 WhatsApp Business integrado",
            "descripcion": "Contacto directo con clientes - ¡Completado!",
            "accion_url": "/whatsapp/configuracion/",
            "template": "onboarding/paso_whatsapp.html",
        },
    }

    if paso not in pasos:
        return redirect("taller:dashboard_suscripciones")

    context = {
        "paso_actual": paso,
        "paso_info": pasos[paso],
        "total_pasos": len(pasos),
        "progreso": (paso / len(pasos)) * 100,
    }

    return render(request, pasos[paso]["template"], context)
