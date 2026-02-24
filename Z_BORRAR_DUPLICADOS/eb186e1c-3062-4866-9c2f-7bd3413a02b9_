"""
Vistas específicas para Perú 🇵🇪
"""

from decimal import Decimal

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import activate, get_language
from django.views.generic import TemplateView

from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.models.ubicacion import Estado, Ciudad


class PELocalizationView(TemplateView):
    """Vista principal para demostrar la localización Perú"""

    template_name = "taller/pe_localization_demo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Datos de localización para Perú
        context.update(
            {
                "estados": Estado.objects.filter(pais="PE").all()[:10],  # Departamentos de Perú
                "marcas_populares": MarcaVehiculo.objects.all()[:8],
                "current_language": get_language(),
                "available_languages": settings.LANGUAGES,
                "pais": "Perú",
                "moneda": "PEN",
                "simbolo_moneda": "S/",
            }
        )

        return context


def api_estados_peru(request):
    """API para obtener departamentos de Perú"""
    estados = Estado.objects.filter(pais="PE").values("id", "nombre", "codigo")
    return JsonResponse({"estados": list(estados)})


def api_ciudades_por_estado_pe(request, estado_id):
    """API para obtener ciudades de un departamento peruano"""
    ciudades = Ciudad.objects.filter(estado_id=estado_id).values("id", "nombre", "poblacion")
    return JsonResponse({"ciudades": list(ciudades)})


def api_marcas_vehiculos_peru(request):
    """API para obtener marcas de vehículos populares en Perú"""
    marcas = MarcaVehiculo.objects.all().values("id", "nombre")
    return JsonResponse({"marcas": list(marcas)})


def api_modelos_por_marca_pe(request):
    """API para obtener modelos de una marca en Perú"""
    marca_id = request.GET.get("marca_id")
    anio = request.GET.get("anio")

    if not marca_id or not anio:
        return JsonResponse({"error": "Marca y año son requeridos"}, status=400)

    modelos = ModeloVehiculo.objects.filter(marca_id=marca_id, anio_desde__lte=anio).values(
        "id", "nombre"
    )

    return JsonResponse({"modelos": list(modelos)})


def api_calcular_impuestos_peru(request):
    """
    API para calcular impuestos en Perú (IGV)
    """
    try:
        subtotal = Decimal(request.GET.get("subtotal", "0"))

        # IGV en Perú es del 18%
        tasa_igv = Decimal("0.18")

        # Calcular impuestos
        igv = subtotal * tasa_igv
        total = subtotal + igv

        return JsonResponse(
            {
                "subtotal": float(subtotal),
                "igv": float(igv),
                "total": float(total),
                "tasa_igv": float(tasa_igv * 100),  # En porcentaje
                "moneda": "S/",
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def api_traducir_servicios_pe(request):
    """
    API para servicios comunes en Perú (español peruano)
    """
    servicios_pe = {
        "Oil Change": "Cambio de Aceite",
        "Brake Service": "Servicio de Frenos",
        "Tire Rotation": "Rotación de Llantas",
        "Engine Diagnostic": "Diagnóstico del Motor",
        "Transmission Service": "Servicio de Transmisión",
        "Battery Replacement": "Cambio de Batería",
        "Air Filter": "Filtro de Aire",
        "Wheel Alignment": "Alineación y Balanceo",
        "Suspension": "Suspensión",
        "Exhaust System": "Sistema de Escape",
        "Tire": "Llanta",
        "Wheel": "Aro",
        "Body Shop": "Planchado y Pintura",
        "Paint": "Pintura",
    }

    return JsonResponse({"servicios": servicios_pe})


def cambiar_idioma_pe(request):
    """Vista para cambiar el idioma en Perú (español)"""
    lang_code = request.GET.get("lang", "es")
    activate(lang_code)
    request.session["django_language"] = lang_code

    # Redirigir a la página anterior
    from django.shortcuts import redirect

    return redirect(request.headers.get("referer", "/pe/"))


def demo_peru_personalization(request):
    """
    Demo de personalización para el mercado peruano
    Muestra características específicas de Perú
    """
    context = {
        "departamentos_pe": [
            {"codigo": "LIM", "nombre": "Lima", "capital": "Lima"},
            {"codigo": "CUS", "nombre": "Cusco", "capital": "Cusco"},
            {"codigo": "ARE", "nombre": "Arequipa", "capital": "Arequipa"},
            {"codigo": "LAL", "nombre": "La Libertad", "capital": "Trujillo"},
            {"codigo": "LAM", "nombre": "Lambayeque", "capital": "Chiclayo"},
            {"codigo": "PIU", "nombre": "Piura", "capital": "Piura"},
            {"codigo": "CAJ", "nombre": "Cajamarca", "capital": "Cajamarca"},
            {"codigo": "JUN", "nombre": "Junín", "capital": "Huancayo"},
            {"codigo": "PUN", "nombre": "Puno", "capital": "Puno"},
            {"codigo": "ICA", "nombre": "Ica", "capital": "Ica"},
        ],
        "marcas_populares_pe": [
            "Toyota",
            "Hyundai",
            "Kia",
            "Nissan",
            "Chevrolet",
            "Volkswagen",
            "Mazda",
            "Honda",
            "Suzuki",
            "Mitsubishi",
        ],
        "moeda": "Sol (S/)",
        "idioma": "Español",
        "formato_data": "DD/MM/YYYY",
        "pais": "Perú",
    }

    return render(request, "taller/pe/demo_personalization.html", context)
