from django.views.generic import TemplateView
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.translation import get_language, activate
from django.conf import settings
from taller.models.ubicacion import Estado, Ciudad
from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.utils.us_localization import USDCurrencyMixin, USTaxCalculator, USServiceTranslator
from decimal import Decimal

class USLocalizationView(TemplateView):
    """Vista principal para demostrar la localización USA"""
    template_name = 'taller/us_localization_demo.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Datos de localización
        context.update({
            'estados': Estado.objects.all()[:10],  # Primeros 10 estados
            'marcas_usa': MarcaVehiculo.objects.filter(pais_origen='USA')[:5],
            'marcas_japonesas': MarcaVehiculo.objects.filter(pais_origen='Japan')[:5],
            'servicios_bilingue': USServiceTranslator.get_servicios_bilingue()[:8],
            'current_language': get_language(),
            'available_languages': settings.LANGUAGES,
        })
        
        # Ejemplo de cálculo de impuestos para Atlanta
        tax_calculator = USTaxCalculator()
        tax_demo = tax_calculator.calcular_total_con_tax(Decimal('100.00'))
        context['tax_demo'] = tax_demo
        
        # Formateo de moneda
        context['currency_examples'] = [
            USDCurrencyMixin.format_usd(99.95),
            USDCurrencyMixin.format_usd(1234.56),
            USDCurrencyMixin.format_usd(15000),
        ]
        
        return context

def api_estados_usa(request):
    """API para obtener estados de EE.UU."""
    estados = Estado.objects.all().values('id', 'nombre', 'codigo', 'sales_tax', 'timezone')
    return JsonResponse({'estados': list(estados)})

def api_ciudades_por_estado(request, estado_id):
    """API para obtener ciudades por estado"""
    try:
        ciudades = Ciudad.objects.filter(estado_id=estado_id).values(
            'id', 'nombre', 'poblacion', 'sales_tax_local', 'es_capital'
        )
        return JsonResponse({'ciudades': list(ciudades)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def api_marcas_vehiculos_usa(request):
    """API para obtener marcas de vehículos del mercado USA"""
    pais = request.GET.get('pais', 'USA')
    marcas = MarcaVehiculo.objects.filter(
        pais_origen=pais, 
        activa=True
    ).values('id', 'nombre', 'nombre_en', 'pais_origen', 'anio_inicio', 'anio_fin')
    
    return JsonResponse({
        'marcas': list(marcas),
        'total': len(marcas)
    })

def api_modelos_por_marca(request, marca_id):
    """API para obtener modelos por marca"""
    try:
        modelos = ModeloVehiculo.objects.filter(
            marca_id=marca_id,
            activo=True
        ).values('id', 'nombre', 'nombre_en', 'tipo_vehiculo', 'anio_inicio', 'anio_fin')
        
        # Agregar rango de años a cada modelo
        modelos_con_anos = []
        for modelo in modelos:
            modelo['anos_disponibles'] = list(range(
                modelo['anio_inicio'], 
                (modelo['anio_fin'] or 2025) + 1
            ))
            modelos_con_anos.append(modelo)
        
        return JsonResponse({
            'modelos': modelos_con_anos,
            'total': len(modelos_con_anos)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def api_calcular_impuestos_usa(request):
    """API para calcular impuestos USA"""
    try:
        subtotal = Decimal(request.GET.get('subtotal', '0'))
        estado_id = request.GET.get('estado_id')
        ciudad_id = request.GET.get('ciudad_id')
        
        calculator = USTaxCalculator(estado=estado_id, ciudad=ciudad_id)
        resultado = calculator.calcular_total_con_tax(subtotal)
        
        # Formatear como USD
        return JsonResponse({
            'subtotal_formatted': USDCurrencyMixin.format_usd(resultado['subtotal']),
            'tax_formatted': USDCurrencyMixin.format_usd(resultado['tax']),
            'total_formatted': USDCurrencyMixin.format_usd(resultado['total']),
            'tax_rate': float(resultado['tax_rate']),
            'raw_values': {
                'subtotal': float(resultado['subtotal']),
                'tax': float(resultado['tax']),
                'total': float(resultado['total'])
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def api_traducir_servicios(request):
    """API para traducir servicios al inglés"""
    servicio_es = request.GET.get('servicio', '')
    traduccion = USServiceTranslator.traducir_servicio(servicio_es)
    
    return JsonResponse({
        'original': servicio_es,
        'traducido': traduccion,
        'servicios_disponibles': USServiceTranslator.get_servicios_bilingue()
    })

def cambiar_idioma(request):
    """Vista para cambiar idioma de la aplicación"""
    idioma = request.POST.get('idioma', 'es')
    
    if idioma in ['es', 'en']:
        activate(idioma)
        request.session['django_language'] = idioma
        
        return JsonResponse({
            'success': True,
            'nuevo_idioma': idioma,
            'mensaje': 'Idioma cambiado exitosamente' if idioma == 'es' else 'Language changed successfully'
        })
    
    return JsonResponse({'success': False, 'error': 'Idioma no válido'})

def demo_atlanta_personalization(request):
    """Demo específico para personalización de Atlanta"""
    
    # Datos específicos de Atlanta
    atlanta = Ciudad.objects.filter(nombre='Atlanta', estado__codigo='GA').first()
    
    context = {
        'ciudad': atlanta,
        'timezone_local': 'America/New_York',  # Eastern Time
        'marcas_populares_atlanta': MarcaVehiculo.objects.filter(
            pais_origen__in=['USA', 'Japan']
        )[:8],
        'servicios_atlanta': [
            {'es': 'Inspección de emisiones', 'en': 'Emissions Testing'},
            {'es': 'Servicio de A/C (verano)', 'en': 'A/C Service (Summer)'},
            {'es': 'Preparación para invierno', 'en': 'Winter Preparation'},
            {'es': 'Cambio de aceite sintético', 'en': 'Synthetic Oil Change'},
        ]
    }
    
    if atlanta:
        tax_calculator = USTaxCalculator(ciudad=atlanta.id)
        context['tax_info'] = tax_calculator.calcular_total_con_tax(Decimal('250.00'))
    
    return render(request, 'taller/atlanta_demo.html', context)
