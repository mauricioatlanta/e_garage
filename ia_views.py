from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def sugerencias_ia(request):
    """Vista para mostrar las sugerencias de IA básica"""
    
    # Datos de ejemplo para la demo
    sugerencias_por_vehiculo = {
        'toyota': {
            'servicios_comunes': [
                {'nombre': 'Cambio de aceite y filtro', 'precio': 25000, 'frecuencia': '10,000 km'},
                {'nombre': 'Revisión de frenos', 'precio': 35000, 'frecuencia': '20,000 km'},
                {'nombre': 'Cambio de filtro de aire', 'precio': 15000, 'frecuencia': '15,000 km'},
                {'nombre': 'Alineación y balanceo', 'precio': 45000, 'frecuencia': '15,000 km'},
                {'nombre': 'Cambio de bujías', 'precio': 30000, 'frecuencia': '30,000 km'},
            ],
            'repuestos_frecuentes': [
                {'nombre': 'Filtro de aceite Toyota original', 'precio': 8500, 'codigo': 'FO-TOY-001'},
                {'nombre': 'Aceite 5W30 sintético', 'precio': 12000, 'codigo': 'AC-5W30'},
                {'nombre': 'Pastillas de freno delanteras', 'precio': 25000, 'codigo': 'PF-TOY-DEL'},
                {'nombre': 'Filtro de aire Toyota', 'precio': 6500, 'codigo': 'FA-TOY-001'},
            ],
            'alertas': [
                'Revisa el sistema de frenos cada 20,000 km',
                'Toyota recomienda aceite sintético para mejor rendimiento',
                'Verifica la cadena de distribución a los 100,000 km'
            ]
        },
        'nissan': {
            'servicios_comunes': [
                {'nombre': 'Servicio de mantenimiento CVT', 'precio': 55000, 'frecuencia': '40,000 km'},
                {'nombre': 'Cambio de aceite Nissan', 'precio': 28000, 'frecuencia': '10,000 km'},
                {'nombre': 'Revisión de transmisión', 'precio': 40000, 'frecuencia': '30,000 km'},
                {'nombre': 'Cambio de correa de distribución', 'precio': 65000, 'frecuencia': '80,000 km'},
            ],
            'repuestos_frecuentes': [
                {'nombre': 'Filtro CVT Nissan', 'precio': 15000, 'codigo': 'FC-NIS-CVT'},
                {'nombre': 'Aceite CVT NS-2', 'precio': 18000, 'codigo': 'AC-CVT-NS2'},
                {'nombre': 'Sensor de oxígeno Nissan', 'precio': 35000, 'codigo': 'SO-NIS-001'},
            ]
        },
        'general': {
            'servicios_comunes': [
                {'nombre': 'Diagnóstico computarizado', 'precio': 20000, 'frecuencia': 'Según síntomas'},
                {'nombre': 'Cambio de aceite estándar', 'precio': 20000, 'frecuencia': '8,000 km'},
                {'nombre': 'Revisión general', 'precio': 30000, 'frecuencia': '15,000 km'},
                {'nombre': 'Lavado de inyectores', 'precio': 40000, 'frecuencia': '30,000 km'},
            ]
        }
    }
    
    context = {
        'sugerencias_por_vehiculo': sugerencias_por_vehiculo,
        'demo_activo': True
    }
    
    return render(request, 'ia/sugerencias_basicas.html', context)

@csrf_exempt
def obtener_sugerencias_vehiculo(request):
    """API para obtener sugerencias según el vehículo"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            marca = data.get('marca', '').lower()
            modelo = data.get('modelo', '').lower()
            anio = data.get('anio', 2020)
            kilometraje = data.get('kilometraje', 0)
            
            # Lógica de IA básica
            sugerencias = generar_sugerencias_ia(marca, modelo, anio, kilometraje)
            
            return JsonResponse({
                'success': True,
                'sugerencias': sugerencias
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def generar_sugerencias_ia(marca, modelo, anio, kilometraje):
    """Lógica de IA para generar sugerencias personalizadas"""
    
    servicios_sugeridos = []
    repuestos_sugeridos = []
    alertas = []
    
    # Sugerencias basadas en kilometraje
    if kilometraje > 0:
        if kilometraje % 10000 <= 1000:  # Cerca del cambio de aceite
            servicios_sugeridos.append({
                'nombre': 'Cambio de aceite y filtro',
                'precio': 25000,
                'prioridad': 'alta',
                'razon': f'Kilometraje actual: {kilometraje:,} km'
            })
        
        if kilometraje > 20000 and kilometraje % 20000 <= 2000:
            servicios_sugeridos.append({
                'nombre': 'Revisión de frenos',
                'precio': 35000,
                'prioridad': 'media',
                'razon': 'Mantenimiento preventivo recomendado'
            })
        
        if kilometraje > 100000:
            alertas.append('Vehículo de alto kilometraje: revisar componentes críticos')
    
    # Sugerencias basadas en marca
    if marca == 'toyota':
        repuestos_sugeridos.extend([
            {'nombre': 'Filtro de aceite Toyota original', 'precio': 8500},
            {'nombre': 'Aceite 5W30 sintético', 'precio': 12000}
        ])
        alertas.append('Toyota: usar repuestos originales para mejor durabilidad')
    
    elif marca == 'nissan':
        if 'cvt' in modelo.lower() or anio >= 2013:
            servicios_sugeridos.append({
                'nombre': 'Mantenimiento transmisión CVT',
                'precio': 55000,
                'prioridad': 'alta',
                'razon': 'CVT requiere mantenimiento especializado'
            })
        alertas.append('Nissan CVT: cambio de aceite cada 40,000 km')
    
    # Sugerencias basadas en año
    if anio < 2010:
        alertas.append('Vehículo antiguo: revisar mangueras y correas regularmente')
        servicios_sugeridos.append({
            'nombre': 'Revisión de componentes antiguos',
            'precio': 40000,
            'prioridad': 'media',
            'razon': 'Vehículo con más de 15 años'
        })
    
    return {
        'servicios': servicios_sugeridos[:5],  # Máximo 5 sugerencias
        'repuestos': repuestos_sugeridos[:5],
        'alertas': alertas[:3],  # Máximo 3 alertas
        'confianza': 85 if marca in ['toyota', 'nissan'] else 70
    }
