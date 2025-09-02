from django.urls import path, include
import sys
print("CARGANDO taller/taller_main_urls.py", file=sys.stderr)
from django.shortcuts import render
from django.views.generic import TemplateView

from . import taller_views
from .taller_views import debug_cliente_autocomplete, dashboard_suscripciones, renovar_empresa
from .views_extra.views import dashboard
from .views_extra.dashboard_empresa import dashboard_centro_operaciones, dashboard_centro_operaciones_espacial
from .views_extra.ajax import ciudades_por_region
from .views_extra.suscripcion import suscripcion_bloqueada
from .views_extra.views_configuracion import configuracion_empresa, configuracion_tecnicos
from .views_extra.timezone_views import configurar_timezone, cambiar_timezone_ajax, preview_timezone
from .views_extra.landing_usa import landing_usa
from taller.views_extra.bienvenida_usa import bienvenida_usa

from . import ajax_views  # Importar vistas AJAX para formularios jerárquicos
from .views_extra.company_settings_views import (
    company_settings_view, 
    upload_logo_ajax, 
    preview_branding, 
    reset_branding,
    export_branding_config,
    company_settings_api
)

app_name = 'taller'

# Vista temporal del diagnóstico IA
def diagnostico_ia_temp(request):
    # Usar template resolution en lugar de template hardcodeado
    from taller.utils.templates import select_country_lang_template
    from django.utils.translation import get_language
    from django.template.response import TemplateResponse
    
    template_name = select_country_lang_template(
        "reportes/diagnostico_ia.html", 
        getattr(request.user.empresa, 'pais', 'cl').lower(), 
        get_language()
    )
    
    return TemplateResponse(request, template_name, {
        'servicios_crecimiento': [
            {'nombre': 'Cambio de Aceite', 'tasa_crecimiento': 15.5, 'ingresos_mes': 125000},
        ],
        'total_documentos': 1547,
        'fecha_analisis': '23/07/2025'
    })

urlpatterns = [
    path('', TemplateView.as_view(template_name='public/landing_inicio_en.html'), name='landing_inicio'),
    path('chile/', TemplateView.as_view(template_name='onboarding/bienvenida_chile.html'), name='landing_chile'),
    path('usa/', bienvenida_usa, name='landing_usa'),
    path('ajax/ciudades/', ciudades_por_region, name='ajax_ciudades'),
    path('dashboard/', dashboard, name='dashboard'),
    path('centro-operaciones/', dashboard_centro_operaciones, name='centro_operaciones'),
    path('centro-operaciones-espacial/', dashboard_centro_operaciones_espacial, name='centro_operaciones_espacial'),
    path('admin/dashboard/', dashboard_suscripciones, name='dashboard_suscripciones'),
    path('renovar-empresa/<int:empresa_id>/', renovar_empresa, name='renovar_empresa'),
    path('suscripcion-bloqueada/', suscripcion_bloqueada, name='suscripcion_bloqueada'),
    path('debug-autocomplete/', debug_cliente_autocomplete, name='debug_autocomplete'),
    path('configuracion/', configuracion_empresa, name='configuracion'),
    path('configuracion/tecnicos/', configuracion_tecnicos, name='configuracion_tecnicos'),
    
    # === CONFIGURACIÓN DE EMPRESA Y BRANDING ===
    path('settings/', company_settings_view, name='company_settings'),
    path('settings/upload-logo/', upload_logo_ajax, name='upload_logo_ajax'),
    path('settings/preview/', preview_branding, name='preview_branding'),
    path('settings/reset/', reset_branding, name='reset_branding'),
    path('settings/export/', export_branding_config, name='export_branding'),
    path('api/company-settings/', company_settings_api, name='company_settings_api'),
    
    path('test-i18n/', __import__('taller.views_extra.test_i18n_view', fromlist=['test_i18n_view']).test_i18n_view, name='test_i18n'),
    
    # === VISTAS DE PRUEBA MULTILENGUAJE ===
    path('test/country-detection/', __import__('taller.views_extra.test_multilang', fromlist=['test_country_detection']).test_country_detection, name='test_country_detection'),
    path('test/service-search/', __import__('taller.views_extra.test_multilang', fromlist=['test_service_search_api']).test_service_search_api, name='test_service_search'),
    
    # Módulos del sistema
    path('clientes/', include('taller.clientes.urls')),
    path('vehiculos/', include('taller.vehiculos.urls')),
    path('repuestos/', include('taller.repuestos.urls')),
    path('servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios')),
    path('business-intelligence/', include('taller.business_intelligence_urls', namespace='business_intelligence')),
    path('settings/', include('taller.settings.urls', namespace='settings')),
    
    # === AJAX JERÁRQUICO - VEHÍCULOS ===
    # Importar vistas AJAX para formularios jerárquicos
    path('ajax/load-modelos/', ajax_views.load_modelos, name='ajax_load_modelos'),
    path('ajax/load-motores/', ajax_views.load_motores, name='ajax_load_motores'),
    path('ajax/load-cajas/', ajax_views.load_cajas, name='ajax_load_cajas'),
    path('ajax/load-motores-cajas/', ajax_views.load_motores_cajas, name='ajax_load_motores_cajas'),
]

# URLs USA
from taller.views_extra.us_views import (
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

from taller.views_extra.demo_publico import (
    demo_atlanta_publico,
    demo_cotizacion_ajax,
    verificar_codigo_atlanta
)

# Importar APIs del catálogo de vehículos
from taller.api_catalogo_views import (
    api_marcas,
    api_modelos,
    api_estadisticas_catalogo
)

# Importar vista demo del catálogo
from taller.demo_catalogo_views import demo_catalogo_vehiculos

us_patterns = [
    path('demo-usa/', USLocalizationView.as_view(), name='demo_usa'),
    path('demo-atlanta/', demo_atlanta_personalization, name='demo_atlanta'),
    path('demo/atlanta/', demo_atlanta_publico, name='demo_atlanta_publico'),
    path('demo/atlanta/quote/', demo_cotizacion_ajax, name='demo_atlanta_quote'),
    path('demo/atlanta/verify-code/', verificar_codigo_atlanta, name='demo_atlanta_verify_code'),
    path('demo/catalogo-vehiculos/', demo_catalogo_vehiculos, name='demo_catalogo_vehiculos'),
    path('api/estados/', api_estados_usa, name='api_estados'),
    path('api/ciudades/<int:estado_id>/', api_ciudades_por_estado, name='api_ciudades'),
    path('api/marcas-usa/', api_marcas_vehiculos_usa, name='api_marcas_usa'),
    path('api/modelos/<int:marca_id>/', api_modelos_por_marca, name='api_modelos'),
    path('api/calcular-impuestos/', api_calcular_impuestos_usa, name='api_calcular_impuestos'),
    path('api/traducir-servicios/', api_traducir_servicios, name='api_traducir_servicios'),
    # APIs del catálogo de vehículos
    path('api/catalogo/marcas/', api_marcas, name='api_catalogo_marcas'),
    path('api/catalogo/modelos/', api_modelos, name='api_catalogo_modelos'),
    path('api/catalogo/stats/', api_estadisticas_catalogo, name='api_catalogo_stats'),
    # APIs adicionales
    path('api/', include('taller.api.urls', namespace='api')),
    path('admin/monitoring/', include('taller.urls_modules.admin_monitoring')),
    path('emails/', include('taller.emails.urls')),
    path('cambiar-idioma/', cambiar_idioma, name='cambiar_idioma'),
    # AJAX Jerárquico - Vehículos
    path('ajax/load-modelos/', ajax_views.load_modelos, name='ajax_load_modelos'),
    path('ajax/load-motores/', ajax_views.load_motores, name='ajax_load_motores'),
    path('ajax/load-cajas/', ajax_views.load_cajas, name='ajax_load_cajas'),
    path('ajax/load-motores-cajas/', ajax_views.load_motores_cajas, name='ajax_load_motores_cajas'),
]

urlpatterns += us_patterns
