"""
URLs específicas para Chile (español)
    path('taller/servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios_admin')),
    path('taller/documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos')),
    path('taller/reportes/', include('taller.reportes.urls')),
    
    # Servicios también bajo /cl/servicios/ para disponibilidad global del namespace
    path('servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios')),
    
    # Documentos también bajo /cl/documentos/ para disponibilidad global del namespace
    path('documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos_global')),o: /cl/
"""
from django.urls import path, include
import sys
print("CARGANDO taller/urls_extra/chile.py", file=sys.stderr)
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from taller.views_extra.country_views import dashboard_cl_view, test_chile_view
from taller import ajax_views

app_name = 'chile'

urlpatterns = [
    # Dashboard principal Chile
    path('', dashboard_cl_view, name='home'),
    path('dashboard/', dashboard_cl_view, name='dashboard'),
    # Redirección para compatibilidad: /cl/centro-operaciones-espacial/ -> /cl/taller/centro-operaciones-espacial/
    path('centro-operaciones-espacial/', lambda request: HttpResponseRedirect('/cl/taller/centro-operaciones-espacial/')),
    
    # Test endpoint Chile
    path('test/', test_chile_view, name='test'),

    # Login para suscriptores de Chile (redirige al login global, pero aquí puedes poner una vista personalizada si lo deseas)
    path('login/', TemplateView.as_view(template_name='registration/login.html'), name='account_login'),
    
    # Registro para Chile (español por defecto)
    path('registro/', include('onboarding_urls')),
    
    # === AJAX JERÁRQUICO - VEHÍCULOS ===
    path('taller/ajax/load-modelos/', ajax_views.load_modelos, name='ajax_load_modelos'),
    path('taller/ajax/load-motores/', ajax_views.load_motores, name='ajax_load_motores'),
    path('taller/ajax/load-cajas/', ajax_views.load_cajas, name='ajax_load_cajas'),
    path('taller/ajax/load-motores-cajas/', ajax_views.load_motores_cajas, name='ajax_load_motores_cajas'),
    
    # Módulos principales (incluir cuando estén funcionando)
    path('vehiculos/', include(('taller.vehiculos.urls', 'vehiculos'), namespace='vehiculos')),
    path('clientes/', include('taller.clientes.urls')),
    path('repuestos/', include('taller.repuestos.urls')),
    
    # URLs principales de taller (configuración, settings, etc.) - sin prefijo para namespace global
    path('taller/', include(('taller.taller_main_urls', 'taller'), namespace='taller')),
    # Dashboard de suscriptor
    path('', include('taller.analytics.urls_suscriptor')),
    
    # Servicios y documentos con namespace bajo /cl/taller/
    path('taller/servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios_admin')),
    # DOCUMENTOS MOVIDO A gestion_taller/urls.py para evitar duplicación
    # path('taller/documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos')),
    path('taller/reportes/', include('taller.reportes.urls')),
    
        # Servicios también bajo /cl/servicios/ para disponibilidad global del namespace
    path('servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios')),
    
    # DOCUMENTOS MOVIDO A gestion_taller/urls.py para evitar duplicación
    # path('documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos_global')),
    
    # Business Intelligence bajo /cl/business-intelligence/
    path('business-intelligence/', include(('taller.business_intelligence_urls', 'business_intelligence'), namespace='business_intelligence')),
    
    # path('api/', include('taller.api.urls')),
    # path('autocomplete/', include('taller.autocomplete.urls')),
    # path('analytics/', include('taller.analytics.urls')),
    # path('gestion/', include('gestion_taller.urls')),
]
