from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decimal import Decimal
import json
from datetime import datetime, timedelta

def demo_atlanta_publico(request):
    """
    Demo público para Atlanta - sin login requerido
    Usa el template atlanta_publico.html
    """
    # Datos del taller demo
    taller_info = {
        'nombre': 'Peachtree Auto Pro',
        'direccion': '2450 Piedmont Rd NE, Atlanta, GA 30324',
        'telefono': '(404) 555-0123',
        'email': 'info@peachtreeautopro.com',
        'zona_horaria': 'US/Eastern'
    }
    
    # Cliente demo realista
    cliente_demo = {
        'nombre': 'Mike Johnson',
        'telefono': '(404) 555-0187',
        'email': 'mike.johnson@email.com',
        'direccion': '1234 Buckhead Ave, Atlanta, GA 30309'
    }
    
    # Vehículo demo
    vehiculo_demo = {
        'año': 2019,
        'marca': 'Ford',
        'modelo': 'F-150',
        'placa': 'GEO-4521',
        'kilometraje': 87500.0,
        'color': 'Midnight Blue'
    }
    
    # Reportes de IA
    reportes_ia = {
        'servicios_recomendados': [
            {
                'servicio': 'Oil Change & Filter',
                'descripcion': 'Regular maintenance due based on mileage and time interval',
                'prioridad': 'HIGH',
                'debido_en': '500 miles',
                'precio_estimado': 65.00
            },
            {
                'servicio': 'Brake Inspection',
                'descripcion': 'Preventive brake system check recommended for vehicle age',
                'prioridad': 'MEDIUM',
                'debido_en': '2 weeks',
                'precio_estimado': 45.00
            },
            {
                'servicio': 'Transmission Service',
                'descripcion': 'Transmission fluid change due at this mileage interval',
                'prioridad': 'LOW',
                'debido_en': '5,000 miles',
                'precio_estimado': 245.00
            }
        ],
        'alertas_inventario': [
            'Oil filter stock low (8 units remaining)',
            'Brake fluid needs restock by Friday',
            'Transmission fluid: Order recommended for next week'
        ],
        'predicciones_ingresos': {
            'proximo_mes': 18750.00,
            'crecimiento': '+12% from this month'
        }
    }
    
    # Métricas del taller
    metricas_taller = {
        'ventas_hoy': 1850.00,
        'ventas_semana': 12400.00,
        'ventas_mes': 45600.00,
        'clientes_atendidos_mes': 156,
        'servicios_mas_populares': [
            {'nombre': 'Oil Change', 'cantidad': 45, 'ingresos': 2925.00},
            {'nombre': 'Brake Service', 'cantidad': 23, 'ingresos': 2875.00},
            {'nombre': 'A/C Service', 'cantidad': 18, 'ingresos': 1710.00},
        ]
    }
    
    context = {
        'taller_info': taller_info,
        'cliente_demo': cliente_demo,
        'vehiculo_demo': vehiculo_demo,
        'reportes_ia': reportes_ia,
        'metricas_taller': metricas_taller,
        'es_demo_publico': True
    }
    
    return render(request, 'demo/atlanta_publico.html', context)

def demo_atlantatest_publico(request):
    """Demo público completo para talleres de Atlanta - SIN LOGIN REQUERIDO"""
    
    # 🚗 DATOS DEMO REALISTAS PARA ATLANTA
    cliente_demo = {
        'nombre': 'Mike Johnson',
        'telefono': '(404) 555-0123',
        'email': 'mike.johnson@gmail.com',
        'direccion': '1234 Peachtree St, Atlanta, GA 30309',
        'vehiculos': [
            {
                'marca': 'Ford',
                'modelo': 'F-150',
                'año': 2019,
                'color': 'Blue',
                'placa': 'GBR 123',
                'vin': '1FTFW1ET5KFC10312',
                'kilometraje': 45000
            }
        ]
    }
    
    vehiculo_demo = cliente_demo['vehiculos'][0]
    
    # 📊 REPORTES IA SIMULADOS
    reportes_ia = {
        'servicios_recomendados': [
            {
                'servicio': 'Oil Change',
                'prioridad': 'High',
                'debido_en': '2 weeks',
                'precio_estimado': 65.00,
                'descripcion': 'Based on mileage (45,000 mi), oil change is due soon'
            },
            {
                'servicio': 'Brake Inspection',
                'prioridad': 'Medium', 
                'debido_en': '1 month',
                'precio_estimado': 85.00,
                'descripcion': '2019 F-150 typically needs brake check at this mileage'
            },
            {
                'servicio': 'Transmission Service',
                'prioridad': 'Low',
                'debido_en': '6 months',
                'precio_estimado': 245.00,
                'descripcion': 'Preventive maintenance for transmission fluid'
            }
        ],
        'predicciones_ingresos': {
            'este_mes': 2850.00,
            'proximo_mes': 3200.00,
            'crecimiento': '+12.3%'
        },
        'alertas_inventario': [
            'Motor Oil 5W-30 - Low Stock (3 units)',
            'Brake Pads (Ford F-150) - Reorder Soon',
            'Air Filters - Good Stock'
        ]
    }
    
    # 💰 COTIZACIÓN DEMO
    cotizacion_demo = {
        'numero': 'COT-ATL-001',
        'fecha': timezone.now().strftime('%m/%d/%Y'),
        'cliente': cliente_demo['nombre'],
        'vehiculo': f"{vehiculo_demo['año']} {vehiculo_demo['marca']} {vehiculo_demo['modelo']}",
        'servicios': [
            {
                'nombre': 'Full Service Oil Change',
                'descripcion': 'Premium synthetic oil + filter replacement',
                'precio': 65.00
            },
            {
                'nombre': 'Brake Inspection & Adjustment',
                'descripcion': 'Complete brake system check and minor adjustments',
                'precio': 85.00
            }
        ],
        'repuestos': [
            {
                'nombre': 'Synthetic Motor Oil (5 qts)',
                'cantidad': 1,
                'precio_unitario': 35.00,
                'precio_total': 35.00
            },
            {
                'nombre': 'Oil Filter (Ford F-150)',
                'cantidad': 1,
                'precio_unitario': 12.00,
                'precio_total': 12.00
            }
        ]
    }
    
    # Calcular totales con impuestos de Georgia
    subtotal_servicios = sum(s['precio'] for s in cotizacion_demo['servicios'])
    subtotal_repuestos = sum(r['precio_total'] for r in cotizacion_demo['repuestos'])
    subtotal = subtotal_servicios + subtotal_repuestos
    
    # Sales tax Georgia: 4% estado + 4.9% Atlanta = 8.9%
    tax_rate = 8.9
    tax_amount = subtotal * (tax_rate / 100)
    total = subtotal + tax_amount
    
    cotizacion_demo.update({
        'subtotal_servicios': subtotal_servicios,
        'subtotal_repuestos': subtotal_repuestos,
        'subtotal': subtotal,
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'total': total
    })
    
    # 📈 MÉTRICAS DEMO DEL TALLER
    metricas_taller = {
        'ventas_hoy': 450.00,
        'ventas_semana': 2850.00,
        'ventas_mes': 12400.00,
        'clientes_atendidos_mes': 48,
        'servicios_mas_populares': [
            {'nombre': 'Oil Change', 'cantidad': 24, 'ingresos': 1560.00},
            {'nombre': 'Brake Service', 'cantidad': 12, 'ingresos': 1020.00},
            {'nombre': 'AC Service', 'cantidad': 8, 'ingresos': 680.00}
        ],
        'crecimiento_mensual': '+15.3%'
    }
    
    context = {
        'demo_mode': True,
        'cliente_demo': cliente_demo,
        'vehiculo_demo': vehiculo_demo,
        'reportes_ia': reportes_ia,
        'cotizacion_demo': cotizacion_demo,
        'metricas_taller': metricas_taller,
        'taller_info': {
            'nombre': 'Atlanta Pro Auto Shop',
            'direccion': '2456 Piedmont Ave, Atlanta, GA 30324',
            'telefono': '(404) 555-SHOP',
            'email': 'info@atlantaproauto.com'
        }
    }
    
    return render(request, 'demo/atlanta_publico.html', context)

@csrf_exempt
def demo_cotizacion_ajax(request):
    """API para generar cotizaciones demo en tiempo real"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Servicios seleccionados
            servicios_seleccionados = data.get('servicios', [])
            
            # Precios base de servicios populares en Atlanta
            precios_servicios = {
                'oil_change': 65.00,
                'brake_service': 125.00,
                'ac_service': 95.00,
                'transmission_service': 245.00,
                'tire_rotation': 35.00,
                'battery_test': 25.00,
                'diagnostic': 110.00
            }
            
            # Calcular cotización
            total_servicios = 0
            servicios_detalle = []
            
            for servicio_id in servicios_seleccionados:
                if servicio_id in precios_servicios:
                    precio = precios_servicios[servicio_id]
                    total_servicios += precio
                    
                    # Nombres amigables
                    nombres = {
                        'oil_change': 'Full Service Oil Change',
                        'brake_service': 'Complete Brake Service',
                        'ac_service': 'A/C System Service',
                        'transmission_service': 'Transmission Service',
                        'tire_rotation': 'Tire Rotation & Balance',
                        'battery_test': 'Battery Test & Clean',
                        'diagnostic': 'Computer Diagnostic'
                    }
                    
                    servicios_detalle.append({
                        'nombre': nombres[servicio_id],
                        'precio': precio
                    })
            
            # Impuestos Georgia
            tax_rate = 8.9
            tax_amount = total_servicios * (tax_rate / 100)
            total_final = total_servicios + tax_amount
            
            return JsonResponse({
                'success': True,
                'cotizacion': {
                    'servicios': servicios_detalle,
                    'subtotal': round(total_servicios, 2),
                    'tax_rate': tax_rate,
                    'tax_amount': round(tax_amount, 2),
                    'total': round(total_final, 2)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def verificar_codigo_atlanta(request):
    """Verificar código especial ATLANTA2025"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            codigo = data.get('codigo', '').upper().strip()
            
            # Códigos válidos para Atlanta
            codigos_validos = {
                'ATLANTA2025': {
                    'descripcion': 'Free 3-month trial for Atlanta shops',
                    'duracion_meses': 3,
                    'beneficios': [
                        'Unlimited customers and vehicles',
                        'Full reporting and AI features',
                        'US tax calculations included',
                        'Priority support',
                        'Free setup assistance'
                    ]
                },
                'GEORGIA2025': {
                    'descripcion': 'Georgia state special offer',
                    'duracion_meses': 2,
                    'beneficios': [
                        'All core features included',
                        'Georgia tax compliance',
                        'Email support'
                    ]
                },
                'PEACHTREE': {
                    'descripcion': 'Limited time Atlanta metro offer',
                    'duracion_meses': 1,
                    'beneficios': [
                        'Basic features trial',
                        'Standard support'
                    ]
                }
            }
            
            if codigo in codigos_validos:
                info_codigo = codigos_validos[codigo]
                return JsonResponse({
                    'success': True,
                    'codigo_valido': True,
                    'descripcion': info_codigo['descripcion'],
                    'duracion_meses': info_codigo['duracion_meses'],
                    'beneficios': info_codigo['beneficios'],
                    'mensaje': f'¡Código {codigo} válido! Activación extendida por {info_codigo["duracion_meses"]} meses.'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'codigo_valido': False,
                    'mensaje': 'Código no válido. Verifica que esté escrito correctamente.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
