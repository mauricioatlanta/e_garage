"""
Vistas específicas para México 🇲🇽
"""

from decimal import Decimal

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import activate, get_language
from django.views.generic import TemplateView

from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.models.ubicacion import Estado, Ciudad


class MXLocalizationView(TemplateView):
    """Vista principal para demostrar la localización México"""

    template_name = "taller/mx_localization_demo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "estados": Estado.objects.filter(pais="MX").order_by("nombre")[:10],
                "marcas_populares": MarcaVehiculo.objects.all()[:8],
                "current_language": get_language(),
                "available_languages": settings.LANGUAGES,
                "pais": "México",
                "moneda": "MXN",
                "simbolo_moneda": "$",
            }
        )

        return context


def api_estados_mexico(request):
    """API para obtener estados de México"""
    estados = Estado.objects.filter(pais="MX").values("id", "nombre", "codigo")
    return JsonResponse({"estados": list(estados)})


def api_ciudades_por_estado_mx(request, estado_id):
    """API para obtener ciudades de un estado mexicano"""
    ciudades = Ciudad.objects.filter(estado_id=estado_id).values("id", "nombre", "poblacion")
    return JsonResponse({"ciudades": list(ciudades)})


def api_marcas_vehiculos_mexico(request):
    """API para obtener marcas de vehículos populares en México"""
    marcas = MarcaVehiculo.objects.all().values("id", "nombre")
    return JsonResponse({"marcas": list(marcas)})


def api_modelos_por_marca_mx(request):
    """API para obtener modelos de una marca en México"""
    marca_id = request.GET.get("marca_id")
    anio = request.GET.get("anio")

    if not marca_id or not anio:
        return JsonResponse({"error": "Marca y año son requeridos"}, status=400)

    modelos = ModeloVehiculo.objects.filter(marca_id=marca_id, anio_desde__lte=anio).values(
        "id", "nombre"
    )

    return JsonResponse({"modelos": list(modelos)})


def api_calcular_impuestos_mexico(request):
    """
    API para calcular IVA en México (16%)
    """
    try:
        subtotal = Decimal(request.GET.get("subtotal", "0"))

        tasa_iva = Decimal("0.16")
        iva = subtotal * tasa_iva
        total = subtotal + iva

        return JsonResponse(
            {
                "subtotal": float(subtotal),
                "iva": float(iva),
                "total": float(total),
                "tasa_iva": float(tasa_iva * 100),
                "moneda": "MXN",
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def api_traducir_servicios_mx(request):
    """
    API para servicios comunes en México (español neutro)
    """
    servicios_mx = {
        "Oil Change": "Cambio de Aceite",
        "Brake Service": "Servicio de Frenos",
        "Tire Rotation": "Rotación de Llantas",
        "Engine Diagnostic": "Diagnóstico del Motor",
        "Transmission Service": "Servicio de Transmisión",
        "Battery Replacement": "Cambio de Batería",
        "Air Filter": "Cambio de Filtro de Aire",
        "Wheel Alignment": "Alineación y Balanceo",
        "Suspension": "Servicio de Suspensión",
        "Exhaust System": "Sistema de Escape",
        "Detailing": "Detailing / Detallado",
        "Paint": "Pintura Automotriz",
    }

    return JsonResponse({"servicios": servicios_mx})


def cambiar_idioma_mx(request):
    """Vista para cambiar el idioma en México (español)"""
    lang_code = request.GET.get("lang", "es")
    activate(lang_code)
    request.session["django_language"] = lang_code

    from django.shortcuts import redirect

    return redirect(request.headers.get("referer", "/mx/"))


def demo_mexico_personalization(request):
    """
    Demo de personalización para el mercado mexicano
    """
    context = {
        "estados_mx": [
            {"codigo": "CX", "nombre": "Ciudad de México", "capital": "Ciudad de México"},
            {"codigo": "JA", "nombre": "Jalisco", "capital": "Guadalajara"},
            {"codigo": "NL", "nombre": "Nuevo León", "capital": "Monterrey"},
            {"codigo": "PU", "nombre": "Puebla", "capital": "Puebla"},
            {"codigo": "QR", "nombre": "Quintana Roo", "capital": "Chetumal"},
            {"codigo": "BC", "nombre": "Baja California", "capital": "Mexicali"},
            {"codigo": "YU", "nombre": "Yucatán", "capital": "Mérida"},
        ],
        "marcas_populares_mx": [
            "Nissan",
            "Chevrolet",
            "Volkswagen",
            "Toyota",
            "Kia",
            "Mazda",
            "Honda",
            "Hyundai",
            "Ford",
            "Renault",
        ],
        "moneda": "Peso Mexicano (MXN)",
        "idioma": "Español",
        "formato_fecha": "DD/MM/YYYY",
        "pais": "México",
    }

    return render(request, "taller/mx/demo_personalization.html", context)
