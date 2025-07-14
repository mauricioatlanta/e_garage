# gestion_taller/urls.py o e_garage/urls.py
from django.contrib import admin
from taller.admin import admin_site
from django.urls import path, include
from taller.main_views import landing_inicio  # Corregido: importar desde main_views
from taller.views_trial import registro_trial
from taller.views_trial_activate import activar_trial
from taller.dashboard_views import dashboard_view
from taller.main_views_mkt import landing_mecanicos, landing_repuestos, landing_servicios, landing_reportes, landing_clientes, landing_ia


from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from taller.clientes.views import obtener_ciudades

urlpatterns = [
    path('', landing_inicio, name='inicio'),
    path('registro-trial/', registro_trial, name='registro_trial'),
    path('activar-trial/', activar_trial, name='activar_trial'),
    path('admin/', admin_site.urls),
    # API principal de la app (incluye tiendas/crear)
    path('api/', include('taller.api.urls')),
    # Otras rutas API (servicios)
    path("api/", include("taller.servicios.api_urls")),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Ruta directa para login
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('accounts/', include('allauth.urls')),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('inicio-usuarios/', TemplateView.as_view(template_name='taller/inicio_usuarios.html'), name='inicio_usuarios'),
    path('mecanicos/', landing_mecanicos, name='landing_mecanicos'),
    path('repuestos-info/', landing_repuestos, name='landing_repuestos'),
    path('servicios-info/', landing_servicios, name='landing_servicios'),
    path('reportes-info/', landing_reportes, name='landing_reportes'),
    path('clientes-info/', landing_clientes, name='landing_clientes'),
    path('ia-info/', landing_ia, name='landing_ia'),

    # rutas de apps
    path('taller/', include(('taller.urls', 'taller'), namespace='taller')),
    path('clientes/', include(('taller.clientes.urls', 'clientes'), namespace='clientes')),
    path('vehiculos/', include(('taller.vehiculos.urls', 'vehiculos'), namespace='vehiculos')),
    path('reportes/', include(('taller.reportes.urls', 'reportes'), namespace='reportes')),
    path('repuestos/', include(('taller.repuestos.urls', 'repuestos'), namespace='repuestos')),
    path('documentos/', include('taller.documentos.urls')),
    path('autocomplete/', include('taller.autocomplete.urls', namespace='autocomplete')),
    path('servicios/', include(('taller.servicios.urls_servicios', 'servicios'), namespace='servicios')),
    path('api/ciudades/', obtener_ciudades, name='ciudades_por_region'),
    path('api/', include(('taller.servicios.urls_servicios', 'servicios_api'), namespace='servicios_api')),
]
