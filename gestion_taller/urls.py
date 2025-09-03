from django.views.generic import RedirectView
# gestion_taller/urls.py — archivo raíz de URLs con migración a países

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from urllib.parse import urlencode
from taller.views_extra.login_redirector import login_redirector
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog  # 👈 Para catálogo JS
from taller.views.country_aware_auth import country_aware_login

# Importar vistas de trial
from taller.views_extra.views_trial import registro_trial
from taller.views_extra.views_trial_activate import activar_trial


def redirect_to_home(request):
    """Redirige a la página principal basada en el usuario o configuración"""
    # Por defecto redirigir a USA para nuevos usuarios
    return redirect('/us/')


def redirect_qs(to):
    def view(request, **kwargs):
        params = request.GET.copy()
        # Si hay kwargs (por ejemplo, uidb36, key), formatear la URL
        url = to.format(**kwargs) if kwargs else to
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        return redirect(url)
    return view

urlpatterns = [
    # Página de inicio - redirige según el usuario
    path('', redirect_to_home, name='home'),
    
    path('admin/', admin.site.urls),
    # Vista temporal para verificar documentos
    path('verificar-docs/', lambda request: __import__('verificar_docs_view').verificar_documentos(request), name='verificar_docs'),
    
    # URLs de Trial - Sistema de 30 días
    path('registro-trial/', registro_trial, name='registro_trial'),
    path('activar-trial/', activar_trial, name='activar_trial'),
    path('activar/', activar_trial, name='activar_trial_short'),
    
    # Login personalizado con contexto de país
    path('accounts/login/', country_aware_login, name='account_login'),
    # Allauth para el resto de funcionalidades
    path('accounts/', include('allauth.urls')),

    # Wrappers country-aware para login y signup
    path('cl/accounts/login/',  redirect_qs('/accounts/login/')),
    path('us/accounts/login/',  redirect_qs('/accounts/login/')),
    path('cl/accounts/signup/', redirect_qs('/accounts/signup/')),
    path('us/accounts/signup/', redirect_qs('/accounts/signup/')),

    # Redirects amigables para login
    path('cl/login/',  redirect_qs('/cl/accounts/login/')),
    path('us/login/',  redirect_qs('/us/accounts/login/')),

    # Logout
    path('cl/accounts/logout/', redirect_qs('/accounts/logout/')),
    path('us/accounts/logout/', redirect_qs('/accounts/logout/')),

    # Password reset (solicitud + enviado + confirm + completo)
    path('cl/accounts/password/reset/',            redirect_qs('/accounts/password/reset/')),
    path('us/accounts/password/reset/',            redirect_qs('/accounts/password/reset/')),
    path('cl/accounts/password/reset/done/',       redirect_qs('/accounts/password/reset/done/')),
    path('us/accounts/password/reset/done/',       redirect_qs('/accounts/password/reset/done/')),
    path('cl/accounts/password/reset/key/<uidb36>/<key>/', redirect_qs('/accounts/password/reset/key/{uidb36}/{key}/')),
    path('us/accounts/password/reset/key/<uidb36>/<key>/', redirect_qs('/accounts/password/reset/key/{uidb36}/{key}/')),
    path('cl/accounts/password/reset/key/done/',   redirect_qs('/accounts/password/reset/key/done/')),
    path('us/accounts/password/reset/key/done/',   redirect_qs('/accounts/password/reset/key/done/')),

    # Password change
    path('cl/accounts/password/change/',      redirect_qs('/accounts/password/change/')),
    path('us/accounts/password/change/',      redirect_qs('/accounts/password/change/')),
    path('cl/accounts/password/change/done/', redirect_qs('/accounts/password/change/done/')),
    path('us/accounts/password/change/done/', redirect_qs('/accounts/password/change/done/')),

    path('i18n/', include('django.conf.urls.i18n')),  # Selector de idioma
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),  # 👈 Catálogo JS para gettext
    path('changelog/', TemplateView.as_view(template_name='changelog.html'), name='changelog'),
    path('cl/', include('taller.urls_extra.chile')),
    path('us/centro-operaciones-espacial/', TemplateView.as_view(template_name='us/centro_operaciones_espacial.html'), name='us-centro-operaciones-espacial'),
    path('us/', include('taller.urls_extra.usa')),
    path('taller/', include(('taller.urls', 'taller'), namespace='taller')),
    # APIs globales (sin prefijo de país)
    path('api/v1/', include('taller.api.urls')),
    # Namespace global directo para tests y consumo unificado
    path('vehiculos-core/', include(('taller.vehiculos.urls', 'vehiculos'), namespace='vehiculos')),
    # Redirección de documentos sin país a Chile por defecto
    path('documentos/', RedirectView.as_view(url='/cl/documentos/', permanent=False), name='documentos_redirect_root'),
    
    # Redirecciones de compatibilidad para URLs antiguas con patrón duplicado
    path('cl/documentos/cl/', RedirectView.as_view(url='/cl/documentos/', permanent=True)),
    path('us/documentos/us/', RedirectView.as_view(url='/us/documentos/', permanent=True)),
    
    # URLs con prefijo de país específico - EVITAR GRUPOS REGEX DUPLICADOS
    path('cl/documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos_cl')),
    path('us/documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos_us')),
    path('cl/reportes/', RedirectView.as_view(pattern_name='taller:reportes_dashboard'), name='reportes_alias_cl'),
    path('us/reportes/', RedirectView.as_view(pattern_name='taller:reportes_dashboard'), name='reportes_alias_us'),
    # Ruta de seguridad para /login/ global
    path('login/', login_redirector, name='login_redirector'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    """Redirige registro al nivel global (alias para signup)"""

