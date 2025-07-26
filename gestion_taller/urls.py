# gestion_taller/urls.py o e_garage/urls.py
from django.contrib import admin
from taller.admin import admin_site
from django.urls import path, include
from taller.main_views import landing_inicio, landing_premium  # Corregido: importar desde main_views
from taller.views.views_trial import registro_trial
from taller.views.views_trial_activate import activar_trial
from taller.dashboard_views import dashboard_view
from taller.main_views_mkt import landing_mecanicos, landing_repuestos, landing_servicios, landing_reportes, landing_clientes, landing_ia
from taller.views.views_landing import landing_egarage  # Importar la vista de la landing page
from taller.reportes.views import reportes_dashboard, reporte_servicios, reporte_repuestos, dashboard_inteligencia_operativa, diagnostico_ia  # Importar vistas de reportes directamente
from taller.reportes.reportes_avanzados import dashboard_rentabilidad, reportes_rentabilidad, reporte_comparativo_precios, reporte_servicios_subcontratados  # Importar dashboard y reportes de rentabilidad
from demo_reportes_views import demo_reportes_por_fecha


from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from taller.clientes.views import obtener_ciudades
from taller.views.suscripcion import suscripcion_bloqueada, registro
from taller.views.views_suscripciones import suspension, subir_comprobante, estado_suscripcion, precios
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from taller.views.landing_usa import landing_usa
from django.views.generic import TemplateView

urlpatterns = [
    path('usa/', landing_usa, name='landing_usa_short'),
    # Landings internacionales
    path('chile/', TemplateView.as_view(template_name='public/landing_chile.html'), name='landing_chile'),
    path('landing-bilingue/', TemplateView.as_view(template_name='public/landing_inicio_en.html'), name='landing_bilingue'),
    
    # URLs de bienvenida por país
    path('bienvenida/cl/', TemplateView.as_view(template_name='onboarding/bienvenida_chile.html'), name='bienvenida_chile'),
    path('bienvenida/usa/', TemplateView.as_view(template_name='onboarding/bienvenida_usa.html'), name='bienvenida_usa'),
    path('welcome/us/', TemplateView.as_view(template_name='onboarding/bienvenida_usa.html'), name='welcome_usa'),
    
    path('registro/', registro, name='registro'),
    path('suscripcion-bloqueada/', suscripcion_bloqueada, name='suscripcion_bloqueada'),
    
    # Sistema de suscripciones
    path('suspension/', suspension, name='suspension'),
    path('comprobante-pago/', subir_comprobante, name='subir_comprobante'),
    path('api/estado-suscripcion/', estado_suscripcion, name='estado_suscripcion'),
    path('precios/', precios, name='precios'),
    
    path('', landing_inicio, name='inicio'),
    path('landing/', landing_premium, name='landing_premium'),  # Nueva ruta para landing.html
    path('egarage/', landing_egarage, name='landing_egarage'),  # Landing page profesional de eGarage
    path('egarage-pro/', landing_egarage, name='landing_egarage_pro'),  # Alternativa en /egarage-pro/
    path('registro-trial/', registro_trial, name='registro_trial'),
    path('activar-trial/', activar_trial, name='activar_trial'),
    path('activar/', activar_trial),
    path('admin/', admin_site.urls),
    # API principal de la app (incluye tiendas/crear)
    path('api/', include('taller.api.urls')),
    # Otras rutas API (servicios)
    path("api/", include("taller.servicios.api_urls")),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Ruta directa para login
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    # path('accounts/', include(('taller.urls', 'taller'))),  # Eliminado para evitar duplicidad de namespace
    path('accounts/', include('allauth.urls')),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('mecanicos/', landing_mecanicos, name='landing_mecanicos'),
    path('repuestos-info/', landing_repuestos, name='landing_repuestos'),
    path('servicios-info/', landing_servicios, name='landing_servicios'),
    path('reportes-info/', landing_reportes, name='landing_reportes'),
    path('clientes-info/', landing_clientes, name='landing_clientes'),
    path('ia-info/', landing_ia, name='landing_ia'),
    path('landing/usa/', landing_usa, name='landing_usa'),
    
    # Rutas de reportes (directas para evitar imports circulares) - COMENTADAS: Ahora se usan con namespace
    # path('reportes/', reportes_dashboard, name='reportes_dashboard'),
    # path('reportes/servicios/', reporte_servicios, name='reporte_servicios'),
    # path('reportes/repuestos/', reporte_repuestos, name='reporte_repuestos'),
    # path('reportes/inteligencia/', dashboard_inteligencia_operativa, name='inteligencia_operativa'),
    # path('reportes/diagnostico/', diagnostico_ia, name='diagnostico_ia'),
    # path('reportes/dashboard-rentabilidad/', dashboard_rentabilidad, name='dashboard_rentabilidad'),
    # path('reportes/rentabilidad/', reportes_rentabilidad, name='reportes_rentabilidad'),
    # path('reportes/comparativo-precios/', reporte_comparativo_precios, name='reporte_comparativo_precios'),
    # path('reportes/servicios-subcontratados/', reporte_servicios_subcontratados, name='reporte_servicios_subcontratados'),

    # rutas de apps
    path('taller/', include(('taller.urls', 'taller'), namespace='taller')),
    path('clientes/', include(('taller.clientes.urls', 'clientes'), namespace='clientes')),
    path('vehiculos/', include(('taller.vehiculos.urls', 'vehiculos'), namespace='vehiculos')),
    path('repuestos/', include(('taller.repuestos.urls', 'repuestos'), namespace='repuestos')),
    path('reportes/', include(('taller.reportes.urls', 'reportes'), namespace='reportes')),
    # Demo URL sin autenticación
    path('demo/reportes/', demo_reportes_por_fecha, name='demo_reportes'),
    path('documentos/', include('taller.documentos.urls')),
    path('autocomplete/', include('taller.autocomplete.urls', namespace='autocomplete')),
    path('servicios/', include(('taller.servicios.urls_servicios', 'servicios'), namespace='servicios')),
    path('configuracion/', include('taller.configuracion_urls')),
    path('api/ciudades/', obtener_ciudades, name='ciudades_por_region'),
    path('api/', include(('taller.servicios.urls_servicios', 'servicios_api'), namespace='servicios_api')),
]

# 🇺🇸 URLs DIRECTAS PARA LOCALIZACIÓN USA (acceso fácil)
from taller.views.us_views import (
    USLocalizationView,
    demo_atlanta_personalization,
    api_estados_usa,
    api_ciudades_por_estado,
    api_marcas_vehiculos_usa,
    api_modelos_por_marca,
    api_calcular_impuestos_usa,
    api_traducir_servicios,
    cambiar_idioma
)

# 🎯 DEMO PÚBLICO ATLANTA (para marketing)
from taller.views.demo_publico import (
    demo_atlanta_publico,
    demo_cotizacion_ajax,
    verificar_codigo_atlanta
)

usa_patterns = [
    # Demos principales con acceso directo
    path('demo-usa/', USLocalizationView.as_view(), name='demo_usa_directo'),
    path('demo-atlanta/', demo_atlanta_personalization, name='demo_atlanta_directo'),
    
    # 🎯 Demo público Atlanta (SIN LOGIN - para marketing)
    path('demo/atlanta/', demo_atlanta_publico, name='demo_atlanta_publico_directo'),
    path('demo/atlanta/quote/', demo_cotizacion_ajax, name='demo_atlanta_quote_directo'),
    path('demo/atlanta/verify-code/', verificar_codigo_atlanta, name='demo_atlanta_verify_directo'),
    
    # APIs USA con acceso directo
    path('api-usa/estados/', api_estados_usa, name='api_estados_usa'),
    path('api-usa/ciudades/<int:estado_id>/', api_ciudades_por_estado, name='api_ciudades_usa'),
    path('api-usa/marcas/', api_marcas_vehiculos_usa, name='api_marcas_usa'),
    path('api-usa/modelos/<int:marca_id>/', api_modelos_por_marca, name='api_modelos_usa'),
    path('api-usa/impuestos/', api_calcular_impuestos_usa, name='api_impuestos_usa'),
    path('api-usa/servicios/', api_traducir_servicios, name='api_servicios_usa'),
    path('cambiar-idioma/', cambiar_idioma, name='cambiar_idioma_usa'),
]

urlpatterns += usa_patterns

# URLs de internacionalización
urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Servir archivos estáticos en desarrollo
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
