"""
URLs específicas para USA (inglés)
Prefijo: /us/
"""
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import TemplateView
from taller.views_extra.country_views import dashboard_us_view, test_usa_view
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from taller import ajax_views

app_name = 'usa'

urlpatterns = [
    # Dashboard principal USA
    path('', dashboard_us_view, name='home'),
    path('dashboard/', dashboard_us_view, name='dashboard'),
    
    # Test endpoint USA
    path('test/', test_usa_view, name='test'),
    
    # === AJAX JERÁRQUICO - VEHÍCULOS ===
    path('taller/ajax/load-modelos/', ajax_views.load_modelos, name='ajax_load_modelos'),
    path('taller/ajax/load-motores/', ajax_views.load_motores, name='ajax_load_motores'),
    path('taller/ajax/load-cajas/', ajax_views.load_cajas, name='ajax_load_cajas'),
    path('taller/ajax/load-motores-cajas/', ajax_views.load_motores_cajas, name='ajax_load_motores_cajas'),
    
    # Módulos principales
    path('vehiculos/', include(('taller.vehiculos.urls_usa', 'vehiculos_usa'), namespace='vehiculos_usa')),  # /us/vehiculos/
    path('clientes/', include('taller.clientes.urls')),   # /us/clientes/
    path('repuestos/', include('taller.repuestos.urls')), # /us/repuestos/
    
    # URLs principales de taller (configuración, settings, etc.) - sin prefijo para namespace global
    path('', include('taller.taller_main_urls')),
    
    # Servicios y documentos con namespace
    path('servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios')),
    path('documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos')),
    path('taller/reportes/', include(('taller.reportes.urls', 'reportes_usa'), namespace='reportes_usa')),
    path('reports/', include('taller.reportes.urls')),
    # Dashboard de suscriptor
    path('', include('taller.analytics.urls_suscriptor')),
    # path('api/', include('taller.api.urls')),
    # path('autocomplete/', include('taller.autocomplete.urls')),
    # path('analytics/', include('taller.analytics.urls')),
    # path('management/', include('gestion_taller.urls')),
    
    # Login para USA (plantilla reutilizable)
    path('login/', TemplateView.as_view(template_name='registration/login.html'), name='account_login'),
]
