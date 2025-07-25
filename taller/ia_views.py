from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def sugerencias_basicas_demo(request):
    """Vista principal de demo de IA básica"""
    
    # Data de sugerencias por marca para el template
    sugerencias_por_vehiculo = {
        'toyota': {
            'servicios_comunes': [
                {'nombre': 'Cambio de Aceite Toyota 0W-20', 'precio': 85000, 'frecuencia': 'Cada 10,000 km'},
                {'nombre': 'Filtros Toyota Originales', 'precio': 45000, 'frecuencia': 'Cada 20,000 km'},
                {'nombre': 'Revisión Híbrida', 'precio': 180000, 'frecuencia': 'Cada 40,000 km'},
            ],
            'repuestos_frecuentes': [
                {'nombre': 'Filtro de Aceite Toyota', 'precio': 25000, 'codigo': 'TOY-FO-001'},
                {'nombre': 'Pastillas Freno Delanteras', 'precio': 120000, 'codigo': 'TOY-PF-028'},
                {'nombre': 'Correa Distribución', 'precio': 85000, 'codigo': 'TOY-CD-145'},
            ],
            'alertas': [
                'Vehículos Toyota requieren aceite sintético específico',
                'Revisión de batería híbrida recomendada cada 80,000 km',
                'Filtros originales aumentan vida útil del motor en 35%'
            ]
        },
        'nissan': {
            'servicios_comunes': [
                {'nombre': 'Cambio de Aceite Nissan 5W-30', 'precio': 75000, 'frecuencia': 'Cada 8,000 km'},
                {'nombre': 'Alineación CVT Nissan', 'precio': 95000, 'frecuencia': 'Cada 30,000 km'},
                {'nombre': 'Mantenimiento Transmisión CVT', 'precio': 350000, 'frecuencia': 'Cada 60,000 km'},
            ],
            'repuestos_frecuentes': [
                {'nombre': 'Filtro CVT Nissan', 'precio': 65000, 'codigo': 'NIS-CVT-089'},
                {'nombre': 'Bujías Iridium', 'precio': 180000, 'codigo': 'NIS-BUJ-234'},
                {'nombre': 'Sensor MAF', 'precio': 220000, 'codigo': 'NIS-MAF-067'},
            ],
            'alertas': [
                'Transmisiones CVT requieren aceite específico Nissan',
                'Cambio de filtro CVT crítico cada 40,000 km',
                'Sensor MAF común en Nissan después 50,000 km'
            ]
        },
        'general': {
            'servicios_comunes': [
                {'nombre': 'Cambio de Aceite Convencional', 'precio': 65000, 'frecuencia': 'Cada 5,000 km'},
                {'nombre': 'Alineación y Balanceo', 'precio': 75000, 'frecuencia': 'Cada 15,000 km'},
                {'nombre': 'Revisión Frenos', 'precio': 45000, 'frecuencia': 'Cada 20,000 km'},
            ],
            'repuestos_frecuentes': [
                {'nombre': 'Filtro de Aceite Universal', 'precio': 15000, 'codigo': 'UNI-FO-001'},
                {'nombre': 'Pastillas Freno Genéricas', 'precio': 85000, 'codigo': 'UNI-PF-050'},
                {'nombre': 'Filtro de Aire', 'precio': 25000, 'codigo': 'UNI-FA-025'},
            ],
            'alertas': [
                'Mantenimiento preventivo reduce costos en 40%',
                'Revisar frenos cada 20,000 km por seguridad',
                'Cambio de aceite regular aumenta vida del motor'
            ]
        }
    }
    
    context = {
        'sugerencias_por_vehiculo': json.dumps(sugerencias_por_vehiculo),
    }
    
    return render(request, 'ia/sugerencias_basicas.html', context)

def obtener_sugerencias_vehiculo(request, marca):
    """API endpoint para obtener sugerencias de IA por marca"""
    
    sugerencias_data = {
        'toyota': {
            'confianza': 88,
            'servicios_recomendados': [
                {'nombre': 'Cambio de Aceite Sintético Toyota', 'precio': 85000, 'urgencia': 'Media'},
                {'nombre': 'Revisión Sistema Híbrido', 'precio': 150000, 'urgencia': 'Baja'},
            ],
            'repuestos_preventivos': [
                {'nombre': 'Filtro Aire Cabina Toyota', 'precio': 45000, 'stock': 'Disponible'},
                {'nombre': 'Correa Serpentina', 'precio': 75000, 'stock': 'Bajo stock'},
            ],
            'alertas_ia': [
                'Patrón: Clientes Toyota tienden a agrupar servicios - oferta paquetes',
                'Oportunidad: Servicios híbridos tienen 67% más margen',
            ]
        },
        'nissan': {
            'confianza': 82,
            'servicios_recomendados': [
                {'nombre': 'Mantenimiento CVT', 'precio': 280000, 'urgencia': 'Alta'},
                {'nombre': 'Cambio Aceite Específico Nissan', 'precio': 75000, 'urgencia': 'Media'},
            ],
            'repuestos_preventivos': [
                {'nombre': 'Filtro CVT Nissan', 'precio': 65000, 'stock': 'Disponible'},
                {'nombre': 'Sensor Posición Árbol Levas', 'precio': 180000, 'stock': 'Disponible'},
            ],
            'alertas_ia': [
                'Crítico: CVT Nissan requiere mantenimiento específico',
                'Tendencia: Sensores fallan comúnmente después 60,000 km',
            ]
        }
    }
    
    data = sugerencias_data.get(marca.lower(), {
        'confianza': 65,
        'servicios_recomendados': [
            {'nombre': 'Mantenimiento General', 'precio': 75000, 'urgencia': 'Media'},
        ],
        'repuestos_preventivos': [
            {'nombre': 'Filtros Básicos', 'precio': 35000, 'stock': 'Disponible'},
        ],
        'alertas_ia': [
            'Recomendación: Mantenimiento preventivo cada 10,000 km',
        ]
    })
    
    return JsonResponse({
        'success': True,
        'marca': marca,
        'data': data
    })

def demo_sugerencias_vehiculo(request):
    """Demo específico para mostrar capacidades de IA durante onboarding"""
    
    # Datos de demo muy específicos y llamativos
    demo_data = {
        'vehiculo_ejemplo': {
            'marca': 'Toyota',
            'modelo': 'Corolla 2020',
            'kilometraje': '45,000 km',
        },
        'analisis_ia': {
            'confianza': 94,
            'patrones_detectados': [
                'Cliente potencial de alto valor',
                'Patrón de mantenimiento preventivo',
                'Oportunidad de servicios premium'
            ],
            'servicios_sugeridos': [
                {
                    'nombre': 'Paquete Mantenimiento Premium Toyota',
                    'precio': 285000,
                    'margen_estimado': 125000,
                    'probabilidad_venta': 78,
                    'valor_vida_cliente': 1850000
                },
                {
                    'nombre': 'Diagnóstico Computarizado Completo',
                    'precio': 85000,
                    'margen_estimado': 65000,
                    'probabilidad_venta': 89,
                    'valor_vida_cliente': 450000
                }
            ],
            'predicciones': [
                'Cliente retornará en 3.2 meses (confianza 87%)',
                'Necesitará frenos en próximos 8,000 km',
                'Potencial para servicios adicionales: $420,000'
            ]
        },
        'comparativa_sin_ia': {
            'tiempo_analisis': '2 horas manual vs 0.3 segundos IA',
            'precision_recomendaciones': '45% manual vs 87% IA',
            'oportunidades_perdidas': '67% menos con IA'
        }
    }
    
    return render(request, 'ia/demo_vehiculo.html', {
        'demo_data': demo_data
    })

@csrf_exempt
def generar_sugerencias_ia(request):
    """Genera sugerencias inteligentes basadas en datos del vehículo y historial"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            marca = data.get('marca', '').lower()
            modelo = data.get('modelo', '')
            anio = data.get('anio', 0)
            kilometraje = data.get('kilometraje', 0)
            
            # Lógica básica de IA simulada
            sugerencias = {
                'confianza': 75,
                'servicios': [],
                'repuestos': [],
                'alertas': [],
                'valor_estimado': 0
            }
            
            # Reglas por marca
            if marca == 'toyota':
                sugerencias['confianza'] = 88
                if kilometraje > 40000:
                    sugerencias['servicios'].append({
                        'nombre': 'Revisión Sistema Híbrido',
                        'precio': 180000,
                        'urgencia': 'Media',
                        'justificacion': 'Mantenimiento preventivo para vehículos Toyota híbridos'
                    })
                    
            elif marca == 'nissan':
                sugerencias['confianza'] = 82
                if kilometraje > 30000:
                    sugerencias['servicios'].append({
                        'nombre': 'Mantenimiento CVT',
                        'precio': 320000,
                        'urgencia': 'Alta',
                        'justificacion': 'Transmisión CVT Nissan requiere mantenimiento específico'
                    })
            
            # Servicios generales por kilometraje
            if kilometraje > 10000:
                sugerencias['servicios'].append({
                    'nombre': 'Cambio de Aceite',
                    'precio': 65000,
                    'urgencia': 'Alta',
                    'justificacion': 'Mantenimiento básico esencial'
                })
                
            if kilometraje > 20000:
                sugerencias['servicios'].append({
                    'nombre': 'Revisión Frenos',
                    'precio': 75000,
                    'urgencia': 'Media',
                    'justificacion': 'Seguridad y mantenimiento preventivo'
                })
            
            # Calcular valor total estimado
            sugerencias['valor_estimado'] = sum(s['precio'] for s in sugerencias['servicios'])
            
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
