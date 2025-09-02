from django.urls import path, include
from taller import views as taller_views

app_name = 'taller'

urlpatterns = [
    # Incluir las URLs principales de taller
    path('', include('taller.taller_main_urls')),
    
    path('clientes/', include(('taller.clientes.urls', 'clientes'), namespace='clientes')),
    # CORREGIDO: Usar vista unificada country-aware en lugar de urls_chile
    path('vehiculos/', include(('taller.vehiculos.urls', 'vehiculos'), namespace='vehiculos')),
    # Namespace unificado para tests y vistas combinadas (REDUNDANTE - eliminado)
    # path('vehiculos-core/', include(('taller.vehiculos.urls', 'vehiculos'), namespace='vehiculos')),
    path('repuestos/', include(('taller.repuestos.urls', 'repuestos'), namespace='repuestos')),
    path('documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos')),
    path('api/', include(('taller.api.urls', 'api'), namespace='api')),
    path('admin-monitoring/', include(('taller.urls_modules.admin_monitoring', 'admin_monitoring'), namespace='admin_monitoring')),
    path('emails/', include(('taller.emails.urls', 'emails'), namespace='emails')),
    path('business-intelligence/', include(('taller.business_intelligence_urls', 'business_intelligence'), namespace='business_intelligence')),
    path('servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios')),
    # Rutas principales de taller (dashboard, settings, etc.)
    # path('configuracion/', taller_views.configuracion, name='configuracion'),  # Comentado temporalmente
    # Puedes agregar aquí otras rutas globales si es necesario
    path('vehiculos/ajax/', include('taller.ajax_urls')),
]

