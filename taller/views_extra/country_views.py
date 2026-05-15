"""
Views específicas por país para manejo de contexto
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from taller.auth.decorators import login_required_default
from taller.middleware.country_url_migration import get_current_country_from_request


class CountryBaseView(TemplateView):
    """Vista base para manejo de contexto por país"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_country"] = get_current_country_from_request(self.request)
        context["country_name"] = self.get_country_name()
        context["language"] = self.get_country_language()
        return context

    def get_country_name(self):
        """Override en subclases"""
        return "País"

    def get_country_language(self):
        """Override en subclases"""
        return "es"


class ChileHomeView(CountryBaseView):
    """Vista principal para Chile"""

    template_name = "dashboard_chile.html"

    def get_country_name(self):
        return "Chile"

    def get_country_language(self):
        return "es"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "eGarage Chile - Dashboard",
                "welcome_message": "Bienvenido a eGarage Chile",
                "currency": "CLP",
                "currency_symbol": "$",
            }
        )
        return context


class USAHomeView(CountryBaseView):
    """Vista principal para USA"""

    template_name = "dashboard_usa.html"

    def get_country_name(self):
        return "United States"

    def get_country_language(self):
        return "en"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "eGarage USA - Dashboard",
                "welcome_message": "Welcome to eGarage USA",
                "currency": "USD",
                "currency_symbol": "$",
            }
        )
        return context


# Views simples por país
@login_required_default
def dashboard_usa_view(request):
    """Dashboard profesional para USA - Muestra el Centro de Operaciones Espacial si está autenticado"""

    # Si el usuario está autenticado, mostrar el Centro de Operaciones Espacial
    if request.user.is_authenticated:
        try:
            # Verificar que tenga empresa asociada
            empresa = request.user.empresa
        except:
            # Si no tiene empresa, crear una básica
            from taller.models.empresa import Empresa

            empresa, created = Empresa.objects.get_or_create(
                user=request.user,
                defaults={
                    "nombre_taller": f"Workshop of {request.user.username}",
                    "pais": "US",
                },
            )
            request.user.empresa = empresa
            request.user.save()

        # Renderizar el Centro de Operaciones Espacial
        from datetime import timedelta

        from django.shortcuts import render
        from django.utils import timezone

        # Datos básicos para el dashboard - calcular métricas reales
        from taller.models.documento import Documento

        hoy = timezone.now().date()
        hace_7_dias = hoy - timedelta(days=7)
        ayer = hoy - timedelta(days=1)

        # Documentos de hoy
        documentos_hoy = Documento.objects.filter(empresa=empresa, fecha_emision=hoy).count()

        # Documentos de ayer para calcular delta
        documentos_ayer = Documento.objects.filter(empresa=empresa, fecha_emision=ayer).count()

        # Calcular delta (porcentaje de cambio)
        if documentos_ayer > 0:
            documentos_delta = (documentos_hoy - documentos_ayer) / documentos_ayer
        else:
            documentos_delta = 0.0 if documentos_hoy == 0 else 1.0

        # Clientes únicos atendidos esta semana
        clientes_atendidos_semana = (
            Documento.objects.filter(empresa=empresa, fecha_emision__gte=hace_7_dias)
            .values("cliente")
            .distinct()
            .count()
        )

        # Eficiencia: ratio de documentos "cerrados" vs emitidos
        docs_cerrados = Documento.objects.filter(
            empresa=empresa,
            fecha_emision__gte=hace_7_dias,
            tipo__in=["FAC", "OT"],  # Facturas y Órdenes de Trabajo como "cerrados"
        ).count()

        docs_totales_semana = Documento.objects.filter(
            empresa=empresa, fecha_emision__gte=hace_7_dias
        ).count()

        if docs_totales_semana > 0:
            efficiency = docs_cerrados / docs_totales_semana
        else:
            efficiency = 0.0

        context = {
            "empresa": empresa,
            "documentos_hoy": documentos_hoy,
            "documentos_delta": documentos_delta,
            "clientes_atendidos_semana": clientes_atendidos_semana,
            "efficiency": efficiency,
            "page_title": "eGarage USA - Space Command Center",
            "is_usa_market": True,
        }
        return render(request, "taller/us/es/dashboard/centro_operaciones_espacial.html", context)

    # Si no está autenticado, mostrar landing page
    from django.shortcuts import render

    context = {
        "page_title": "eGarage USA - Professional Automotive Management",
        "meta_description": "The all-in-one platform for auto repair shops, parts stores, tire shops and car washes in the United States.",
        "is_usa_market": True,
        "seo_title": "eGarage USA | Professional Automotive Management System",
        "seo_description": "Try eGarage, the most advanced automotive management platform for the US. Professional features, sales tax compliance, and modern design.",
        "og_image": "/static/img/og_usa_landing.png",
    }
    return render(request, "us/en/landing_usa_enhanced.html", context)


@login_required_default
def dashboard_cl_view(request):
    """Dashboard profesional para Chile - Redirige al Centro de Operaciones Espacial si está autenticado"""

    # Si el usuario está autenticado, redirigir al Centro de Operaciones Espacial
    if request.user.is_authenticated:
        try:
            # Verificar que tenga empresa asociada
            empresa = request.user.empresa
            # Detectar país y redirigir a la ruta correcta
            from django.shortcuts import redirect

            if hasattr(request.user, "pais") and request.user.pais == "US":
                return redirect("/us/centro-operaciones/")
            else:
                return redirect("/cl/es/centro-operaciones/")
        except:
            # Si no tiene empresa, crear una básica
            from taller.models.empresa import Empresa

            empresa, created = Empresa.objects.get_or_create(
                user=request.user,
                defaults={"nombre_taller": f"Taller de {request.user.username}"},
            )
            from django.shortcuts import redirect

            if hasattr(request.user, "pais") and request.user.pais == "US":
                return redirect("/us/centro-operaciones/")
            else:
                return redirect("/cl/es/centro-operaciones/")

    # Si no está autenticado, mostrar página de bienvenida
    planes = [
        {
            "nombre": "1 Mes",
            "precio": 20000,
            "detalle": "Menos de $700 diarios - IVA incluido, sin letra chica",
            "badge": None,
        },
        {
            "nombre": "6 Meses",
            "precio": 110000,
            "detalle": "Ahorra $10.000 CLP - IVA incluido, sin letra chica",
            "badge": "Más Popular",
        },
        {
            "nombre": "1 Año",
            "precio": 200000,
            "detalle": "Ahorra $40.000 CLP - IVA incluido, sin letra chica",
            "badge": "Mejor Valor",
        },
    ]
    testimonios = [
        {
            "nombre": "Carlos M.",
            "ciudad": "Valparaíso",
            "texto": "Antes no podía saber cuánto ganaba cada mecánico. Hoy sé en tiempo real quién rinde más.",
            "avatar": "avatars/carlos.png",
        },
        {
            "nombre": "Paula R.",
            "ciudad": "Santiago",
            "texto": "Me sobraban repuestos sin vender. Ahora no pierdo stock ni plata.",
            "avatar": "avatars/paula.png",
        },
        {
            "nombre": "Diego A.",
            "ciudad": "Viña del Mar",
            "texto": "Lo que hoy hago en 10 minutos, antes me tomaba 3 horas con libreta y lápiz.",
            "avatar": "avatars/diego.png",
        },
    ]
    diferenciales = [
        {
            "icon": "chart-bar",
            "titulo": "WhatsApp integrado",
            "desc": "Envía presupuestos, recibos y recordatorios directamente a tus clientes con un clic.",
        },
        {
            "icon": "package",
            "titulo": "100% accesible",
            "desc": "$20.000 al mes → menos de $700 diarios. Pensado para talleres chicos y medianos.",
        },
        {
            "icon": "receipt",
            "titulo": "Todo en uno",
            "desc": "Clientes, vehículos, repuestos, servicios, facturación y reportes en una sola plataforma.",
        },
        {
            "icon": "bot",
            "titulo": "Enfocado en rentabilidad",
            "desc": "No solo gestiona, te muestra dónde ganas y dónde pierdes dinero.",
        },
        {
            "icon": "users",
            "titulo": "Escalable para crecer",
            "desc": "Si creces, eGarage crece contigo. Desde talleres familiares hasta grandes centros.",
        },
        {
            "icon": "store",
            "titulo": "Para casas de repuestos",
            "desc": "Digitaliza tu bodega, catálogos digitales y control de stock en tiempo real.",
        },
    ]
    frases = {
        "headline": "Deja atrás la libreta y el lápiz",
        "sub": "Administra tu taller con tecnología de nivel mundial. Factura, estimados y recibos directo a WhatsApp 📲. Un precio accesible para que incluso el taller más pequeño pueda ser digital.",
    }

    context = {
        "current_country": "CL",
        "country_name": "Chile",
        "language": "es",
        "page_title": "eGarage Chile - Gestión Automotriz Profesional",
        "welcome_message": "Bienvenido a eGarage Chile",
        "currency": "CLP",
        "currency_symbol": "$",
        "planes": planes,
        "testimonios": testimonios,
        "diferenciales": diferenciales,
        "frases": frases,
        "moneda": "CLP",
        "idioma": "ES",
    }
    return render(request, "onboarding/bienvenida_chile.html", context)


def dashboard_us_view(request):
    """Dashboard simple para USA"""
    context = {
        "current_country": "US",
        "country_name": "United States",
        "language": "en",
        "page_title": "eGarage USA - Professional Workshop Management",
        "welcome_message": "Welcome to eGarage USA",
        "currency": "USD",
        "currency_symbol": "$",
    }
    return render(request, "dashboard_usa.html", context)


# Views de test por país
def test_chile_view(request):
    """Endpoint de test para Chile"""
    return JsonResponse(
        {
            "status": "success",
            "country": "CL",
            "message": "Test Chile funcionando correctamente",
            "timestamp": str(timezone.now()),
        }
    )


def test_usa_view(request):
    """Endpoint de test para USA"""
    return JsonResponse(
        {
            "status": "success",
            "country": "US",
            "message": "Test USA working correctly",
            "timestamp": str(timezone.now()),
        }
    )


# API endpoints de país
def api_country_info(request):
    """API que retorna información del país actual"""
    country = get_current_country_from_request(request)

    country_info = {
        "CL": {
            "name": "Chile",
            "language": "es",
            "currency": "CLP",
            "timezone": "America/Santiago",
            "phone_code": "+56",
        },
        "US": {
            "name": "United States",
            "language": "en",
            "currency": "USD",
            "timezone": "America/New_York",
            "phone_code": "+1",
        },
    }

    return JsonResponse(
        {
            "country_code": country,
            "country_info": country_info.get(country, {}),
            "detected_from": "url_prefix",
        }
    )


# Import timezone
from django.utils import timezone
