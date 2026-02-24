"""
Vistas específicas para Venezuela 🇻🇪
"""

from decimal import Decimal

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import activate, get_language
from django.views.generic import TemplateView

from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.models.ubicacion import Estado, Ciudad


class VELocalizationView(TemplateView):
    """Vista principal para demostrar la localización Venezuela"""

    template_name = "taller/ve_localization_demo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Datos de localización para Venezuela
        context.update(
            {
                "estados": Estado.objects.filter(pais="VE").all()[:10],  # Estados de Venezuela
                "marcas_populares": MarcaVehiculo.objects.all()[:8],
                "current_language": get_language(),
                "available_languages": settings.LANGUAGES,
                "pais": "Venezuela",
                "moneda": "VES",
                "simbolo_moneda": "Bs.",
            }
        )

        return context


def api_estados_venezuela(request):
    """API para obtener estados de Venezuela"""
    estados = Estado.objects.filter(pais="VE").values("id", "nombre", "codigo")
    return JsonResponse({"estados": list(estados)})


def api_ciudades_por_estado_ve(request, estado_id):
    """API para obtener ciudades de un estado venezolano"""
    ciudades = Ciudad.objects.filter(estado_id=estado_id).values("id", "nombre", "poblacion")
    return JsonResponse({"ciudades": list(ciudades)})


def api_marcas_vehiculos_venezuela(request):
    """API para obtener marcas de vehículos populares en Venezuela"""
    marcas = MarcaVehiculo.objects.all().values("id", "nombre")
    return JsonResponse({"marcas": list(marcas)})


def api_modelos_por_marca_ve(request):
    """API para obtener modelos de una marca en Venezuela"""
    marca_id = request.GET.get("marca_id")
    anio = request.GET.get("anio")

    if not marca_id or not anio:
        return JsonResponse({"error": "Marca y año son requeridos"}, status=400)

    modelos = ModeloVehiculo.objects.filter(marca_id=marca_id, anio_desde__lte=anio).values(
        "id", "nombre"
    )

    return JsonResponse({"modelos": list(modelos)})


def api_calcular_impuestos_venezuela(request):
    """
    API para calcular impuestos en Venezuela (IVA)
    """
    try:
        subtotal = Decimal(request.GET.get("subtotal", "0"))

        # IVA en Venezuela es del 16%
        tasa_iva = Decimal("0.16")

        # Calcular impuestos
        iva = subtotal * tasa_iva
        total = subtotal + iva

        return JsonResponse(
            {
                "subtotal": float(subtotal),
                "iva": float(iva),
                "total": float(total),
                "tasa_iva": float(tasa_iva * 100),  # En porcentaje
                "moneda": "Bs.",
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def api_traducir_servicios_ve(request):
    """
    API para servicios comunes en Venezuela (español venezolano)
    """
    servicios_ve = {
        "Oil Change": "Cambio de Aceite",
        "Brake Service": "Servicio de Frenos",
        "Tire Rotation": "Rotación de Cauchos",
        "Engine Diagnostic": "Diagnóstico del Motor",
        "Transmission Service": "Servicio de Transmisión",
        "Battery Replacement": "Cambio de Batería",
        "Air Filter": "Filtro de Aire",
        "Wheel Alignment": "Alineación y Balanceo",
        "Suspension": "Suspensión",
        "Exhaust System": "Sistema de Escape",
        "Tire": "Caucho",
        "Wheel": "Rin",
        "Body Shop": "Latonería",
        "Paint": "Pintura",
    }

    return JsonResponse({"servicios": servicios_ve})


def cambiar_idioma_ve(request):
    """Vista para cambiar el idioma en Venezuela (español)"""
    lang_code = request.GET.get("lang", "es")
    activate(lang_code)
    request.session["django_language"] = lang_code

    # Redirigir a la página anterior
    from django.shortcuts import redirect

    return redirect(request.headers.get("referer", "/ve/"))


def demo_venezuela_personalization(request):
    """
    Demo de personalización para el mercado venezolano
    Muestra características específicas de Venezuela
    """
    context = {
        "estados_ve": [
            {"codigo": "DC", "nombre": "Distrito Capital", "capital": "Caracas"},
            {"codigo": "AM", "nombre": "Amazonas", "capital": "Puerto Ayacucho"},
            {"codigo": "AN", "nombre": "Anzoátegui", "capital": "Barcelona"},
            {"codigo": "AP", "nombre": "Apure", "capital": "San Fernando de Apure"},
            {"codigo": "AR", "nombre": "Aragua", "capital": "Maracay"},
            {"codigo": "BA", "nombre": "Barinas", "capital": "Barinas"},
            {"codigo": "BO", "nombre": "Bolívar", "capital": "Ciudad Bolívar"},
            {"codigo": "CA", "nombre": "Carabobo", "capital": "Valencia"},
            {"codigo": "CO", "nombre": "Cojedes", "capital": "San Carlos"},
            {"codigo": "DA", "nombre": "Delta Amacuro", "capital": "Tucupita"},
        ],
        "marcas_populares_ve": [
            "Chevrolet",
            "Ford",
            "Toyota",
            "Jeep",
            "Mazda",
            "Hyundai",
            "Kia",
            "Nissan",
            "Mitsubishi",
            "Chery",
        ],
        "moeda": "Bolívar (Bs.)",
        "idioma": "Español",
        "formato_data": "DD/MM/YYYY",
        "pais": "Venezuela",
    }

    return render(request, "taller/ve/demo_personalization.html", context)
