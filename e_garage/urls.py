
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Portal de clientes
    path('portal/', include('taller.urls.portal_urls')),
    # Onboarding gratuito
    path('registro/', include('onboarding_urls')),
    # Registro moderno por país
    path('signup/', include('urls_signup')),
    # Solo una inclusión principal para las rutas de la app
    path('', include('taller.urls')),
]
