"""
Vistas específicas para Brasil 🇧🇷
"""

from decimal import Decimal

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import activate, get_language
from django.views.generic import TemplateView

from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.models.ubicacion import Estado, Ciudad


class BRLocalizationView(TemplateView):
    """Vista principal para demostrar la localización Brasil"""

    template_name = "taller/br_localization_demo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Datos de localización para Brasil
        context.update(
            {
                "estados": Estado.objects.filter(pais="BR").all()[:10],  # Estados de Brasil
                "marcas_populares": MarcaVehiculo.objects.all()[:8],
                "current_language": get_language(),
                "available_languages": settings.LANGUAGES,
                "pais": "Brasil",
                "moneda": "BRL",
                "simbolo_moneda": "R$",
            }
        )

        return context


def api_estados_brasil(request):
    """API para obtener estados de Brasil"""
    estados = Estado.objects.filter(pais="BR").values("id", "nome", "sigla", "codigo_ibge")
    return JsonResponse({"estados": list(estados)})


def api_ciudades_por_estado_br(request, estado_id):
    """API para obtener ciudades de un estado brasileño"""
    ciudades = Ciudad.objects.filter(estado_id=estado_id).values("id", "nome", "codigo_ibge")
    return JsonResponse({"ciudades": list(ciudades)})


def api_marcas_vehiculos_brasil(request):
    """API para obtener marcas de vehículos populares en Brasil"""
    marcas = MarcaVehiculo.objects.all().values("id", "nombre")
    return JsonResponse({"marcas": list(marcas)})


def api_modelos_por_marca_br(request):
    """API para obtener modelos de una marca en Brasil"""
    marca_id = request.GET.get("marca_id")
    anio = request.GET.get("anio")

    if not marca_id or not anio:
        return JsonResponse({"error": "Marca e ano são obrigatórios"}, status=400)

    modelos = ModeloVehiculo.objects.filter(marca_id=marca_id, anio_desde__lte=anio).values(
        "id", "nombre"
    )

    return JsonResponse({"modelos": list(modelos)})


def api_calcular_impuestos_brasil(request):
    """
    API para calcular impuestos en Brasil (ICMS, IPI, ISS según tipo de servicio)
    """
    try:
        subtotal = Decimal(request.GET.get("subtotal", "0"))
        estado = request.GET.get("estado", "SP")  # Por defecto São Paulo
        tipo_servicio = request.GET.get("tipo", "mecanico")  # mecanico, peças, etc.

        # Tasas de ICMS por estado (simplificado - las principales)
        tasas_icms = {
            "SP": Decimal("0.18"),  # São Paulo
            "RJ": Decimal("0.20"),  # Rio de Janeiro
            "MG": Decimal("0.18"),  # Minas Gerais
            "RS": Decimal("0.18"),  # Rio Grande do Sul
            "PR": Decimal("0.18"),  # Paraná
            "SC": Decimal("0.17"),  # Santa Catarina
            "BA": Decimal("0.18"),  # Bahia
            "PE": Decimal("0.18"),  # Pernambuco
            "CE": Decimal("0.18"),  # Ceará
            "DF": Decimal("0.18"),  # Distrito Federal
        }

        # Obtener tasa de ICMS para el estado
        tasa_icms = tasas_icms.get(estado, Decimal("0.18"))

        # ISS (Imposto sobre Serviços) - generalmente 2-5%
        tasa_iss = Decimal("0.05") if tipo_servicio == "mecanico" else Decimal("0.00")

        # Calcular impuestos
        icms = subtotal * tasa_icms
        iss = subtotal * tasa_iss
        total_impuestos = icms + iss
        total = subtotal + total_impuestos

        return JsonResponse(
            {
                "subtotal": float(subtotal),
                "icms": float(icms),
                "iss": float(iss),
                "total_impuestos": float(total_impuestos),
                "total": float(total),
                "estado": estado,
                "tasa_icms": float(tasa_icms * 100),  # En porcentaje
                "tasa_iss": float(tasa_iss * 100),  # En porcentaje
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def api_traducir_servicios_br(request):
    """
    API para traducir servicios comunes de inglés/español a portugués brasileño
    """
    servicios_pt = {
        "Oil Change": "Troca de Óleo",
        "Brake Service": "Serviço de Freios",
        "Tire Rotation": "Rodízio de Pneus",
        "Engine Diagnostic": "Diagnóstico do Motor",
        "Transmission Service": "Serviço de Transmissão",
        "Battery Replacement": "Substituição de Bateria",
        "Air Filter": "Filtro de Ar",
        "Wheel Alignment": "Alinhamento de Rodas",
        "Suspension": "Suspensão",
        "Exhaust System": "Sistema de Escapamento",
        # Español a Portugués
        "Cambio de Aceite": "Troca de Óleo",
        "Frenos": "Freios",
        "Neumáticos": "Pneus",
        "Batería": "Bateria",
        "Alineación": "Alinhamento",
    }

    return JsonResponse({"servicios": servicios_pt})


def cambiar_idioma_br(request):
    """Vista para cambiar el idioma en Brasil (pt-br)"""
    lang_code = request.GET.get("lang", "pt-br")
    activate(lang_code)
    request.session["django_language"] = lang_code

    # Redirigir a la página anterior
    from django.shortcuts import redirect

    return redirect(request.headers.get("referer", "/br/"))


def demo_brasil_personalization(request):
    """
    Demo de personalización para el mercado brasileño
    Muestra características específicas de Brasil
    """
    context = {
        "estados_br": [
            {"sigla": "SP", "nome": "São Paulo", "capital": "São Paulo"},
            {"sigla": "RJ", "nome": "Rio de Janeiro", "capital": "Rio de Janeiro"},
            {"sigla": "MG", "nome": "Minas Gerais", "capital": "Belo Horizonte"},
            {"sigla": "RS", "nome": "Rio Grande do Sul", "capital": "Porto Alegre"},
            {"sigla": "BA", "nome": "Bahia", "capital": "Salvador"},
            {"sigla": "PR", "nome": "Paraná", "capital": "Curitiba"},
            {"sigla": "PE", "nome": "Pernambuco", "capital": "Recife"},
            {"sigla": "CE", "nome": "Ceará", "capital": "Fortaleza"},
            {"sigla": "SC", "nome": "Santa Catarina", "capital": "Florianópolis"},
            {"sigla": "DF", "nome": "Distrito Federal", "capital": "Brasília"},
        ],
        "marcas_populares_br": [
            "Volkswagen",
            "Chevrolet",
            "Fiat",
            "Ford",
            "Renault",
            "Hyundai",
            "Toyota",
            "Honda",
            "Nissan",
            "Jeep",
        ],
        "moeda": "Real (R$)",
        "idioma": "Português",
        "formato_data": "DD/MM/YYYY",
        "pais": "Brasil",
    }

    return render(request, "taller/br/demo_personalization.html", context)
