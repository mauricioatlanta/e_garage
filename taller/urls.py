from django.urls import path, include

from . import taller_views
from .taller_views import debug_cliente_autocomplete, dashboard_suscripciones, renovar_empresa
from .views import editar_empresa
from .views.ajax import ciudades_por_region
from taller.registro_views import registro_unificado
from django.shortcuts import render
from taller.models.taller_info import TallerInfo
from taller.models.clientes import Cliente
from taller.models.documento import Documento
from django.db.models import Sum
from django.utils import timezone
from .views.suscripcion import suscripcion_bloqueada, registro, activar

from taller.views.account import EmailConfirmEmptyView
from taller.views.custom_allauth import CustomEmailConfirmView

# Importaciones de configuración
from .views.views_configuracion import configuracion_empresa, configuracion_mecanicos

# 🇺🇸 Importaciones para timezone
from .views.timezone_views import configurar_timezone, cambiar_timezone_ajax, preview_timezone

# 🇺🇸 Importaciones para landing USA
from .views.landing_usa import landing_usa

# Vista temporal del diagnóstico IA
def diagnostico_ia_temp(request):
    return render(request, 'taller/reportes/diagnostico_ia.html', {
        'servicios_crecimiento': [
            {'nombre': 'Cambio de Aceite', 'tasa_crecimiento': 15.5, 'ingresos_mes': 125000},
            {'nombre': 'Alineación', 'tasa_crecimiento': 12.3, 'ingresos_mes': 85000},
            {'nombre': 'Frenos', 'tasa_crecimiento': 9.8, 'ingresos_mes': 195000}
        ],
        'servicios_declive': [
            {'nombre': 'Carburador', 'tasa_declive': -8.2, 'ingresos_mes': 25000},
            {'nombre': 'Distribución Manual', 'tasa_declive': -5.1, 'ingresos_mes': 35000}
        ],
        'estacionalidad': [
            {'temporada': 'Verano', 'tendencia': 'Aumento en aire acondicionado +45%'},
            {'temporada': 'Invierno', 'tendencia': 'Picos en batería y calefacción +32%'}
        ],
        'comparativa_mercado': [
            {'categoria': 'Talleres Premium', 'posicion': 'Top 15%', 'benchmark': 'Superando promedio en 23%'},
            {'categoria': 'Eficiencia Operativa', 'posicion': 'Top 8%', 'benchmark': 'Líder en tiempo de atención'}
        ],
        'recomendaciones_ia': [
            {'accion': 'Expandir servicios eléctricos para vehículos híbridos', 'impacto_estimado': 180000, 'prioridad': 'Alta'},
            {'accion': 'Implementar programa de mantenimiento preventivo', 'impacto_estimado': 125000, 'prioridad': 'Media'},
            {'accion': 'Optimizar inventario de filtros premium', 'impacto_estimado': 67000, 'prioridad': 'Media'}
        ],
        'predicciones_ingresos': [
            {'periodo': '3 meses', 'ingresos_proyectados': 2450000, 'confianza': 89},
            {'periodo': '6 meses', 'ingresos_proyectados': 5200000, 'confianza': 82},
            {'periodo': '12 meses', 'ingresos_proyectados': 11800000, 'confianza': 74}
        ],
        'alertas_criticas': [
            {'tipo': 'Oportunidad', 'descripcion': 'Cliente premium con potencial de 300% más servicios'},
            {'tipo': 'Riesgo', 'descripcion': '15% clientes sin retorno en 60 días - activar retención'},
            {'tipo': 'Tendencia', 'descripcion': 'Demanda eléctrica creciendo 25% mensual'}
        ],
        'insights_ai': [
            {'insight': 'Clientes que realizan alineación tienen 67% más probabilidad de regresar en 3 meses'},
            {'insight': 'Servicios agrupados generan 43% más margen que servicios individuales'},
            {'insight': 'Horario óptimo para servicios premium: 10-12h con 78% satisfacción'}
        ],
        'total_documentos': 1547,
        'fecha_analisis': '23/07/2025'
    })


# Página de inicio por defecto (bilingüe EN/ES, mercado USA/Latino)
from django.views.generic import TemplateView
urlpatterns = [
    path('', TemplateView.as_view(template_name='public/landing_inicio_en.html'), name='landing_inicio'),
    # Chile: acceso directo
    path('chile/', TemplateView.as_view(template_name='public/landing_chile.html'), name='landing_chile'),
    # USA: acceso directo
    path('usa/', landing_usa, name='landing_usa'),

    # Endpoint AJAX para selects dependientes de ciudad
    path('ajax/ciudades/', ciudades_por_region, name='ajax_ciudades'),

    # ...existing code...
    path('dashboard/', dashboard_suscripciones, name='dashboard_suscripciones'),
    path('suscripcion-bloqueada/', suscripcion_bloqueada, name='suscripcion_bloqueada'),
    path('debug-autocomplete/', debug_cliente_autocomplete, name='debug_autocomplete'),
    path('configuracion/', configuracion_empresa, name='configuracion'),
    path('configuracion/mecanicos/', configuracion_mecanicos, name='configuracion_mecanicos'),
    # ...existing code...
]

# 🇺🇸 AGREGAMOS URLs DE LOCALIZACIÓN USA DIRECTAMENTE
from taller.views.us_views import (
    USLocalizationView,
    api_estados_usa,
    api_ciudades_por_estado,
    api_marcas_vehiculos_usa,
    api_modelos_por_marca,
    api_calcular_impuestos_usa,
    api_traducir_servicios,
    cambiar_idioma,
    demo_atlanta_personalization
)

# Importar vistas del demo público
from taller.views.demo_publico import (
    demo_atlanta_publico,
    demo_atlantatest_publico,
    demo_cotizacion_ajax,
    verificar_codigo_atlanta
)

us_patterns = [
    # Demo principal USA
    path('demo-usa/', USLocalizationView.as_view(), name='demo_usa'),
    
    # Demo específico Atlanta
    path('demo-atlanta/', demo_atlanta_personalization, name='demo_atlanta'),
    
    # Demo público Atlanta (sin login)
    path('demo/atlanta/', demo_atlanta_publico, name='demo_atlanta_publico'),
    path('demo/atlanta/quote/', demo_cotizacion_ajax, name='demo_atlanta_quote'),
    path('demo/atlanta/verify-code/', verificar_codigo_atlanta, name='demo_atlanta_verify_code'),
    
    # APIs de localización
    path('api/estados/', api_estados_usa, name='api_estados'),
    path('api/ciudades/<int:estado_id>/', api_ciudades_por_estado, name='api_ciudades'),
    path('api/marcas-usa/', api_marcas_vehiculos_usa, name='api_marcas_usa'),
    path('api/modelos/<int:marca_id>/', api_modelos_por_marca, name='api_modelos'),
    path('api/calcular-impuestos/', api_calcular_impuestos_usa, name='api_calcular_impuestos'),
    path('api/traducir-servicios/', api_traducir_servicios, name='api_traducir_servicios'),
    
    # Panel administrativo de monitoreo
    path('admin/monitoring/', include('taller.urls_modules.admin_monitoring')),
    
    # 📊 Sistema de Analytics AI (Temporalmente deshabilitado)
    # path('analytics/', include('taller.analytics.urls')),
    
    # 📧 Sistema de Emails
    path('emails/', include('taller.emails.urls')),
    
    # Cambio de idioma
    path('cambiar-idioma/', cambiar_idioma, name='cambiar_idioma'),
]

urlpatterns += us_patterns
