from django.urls import path, include
from . import onboarding_views

app_name = 'onboarding'

urlpatterns = [
    # Registro gratuito - landing principal
    path('', onboarding_views.registro_gratuito, name='registro_gratuito'),
    
    # Flujo de onboarding
    path('bienvenida/', onboarding_views.bienvenida_onboarding, name='bienvenida'),
    path('paso/', onboarding_views.onboarding_paso, name='onboarding_paso'),
    
    # Incluir rutas de IA como parte del onboarding
    path('ia/', include('taller.ia_urls', namespace='ia_onboarding')),
]
