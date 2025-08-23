"""
Views específicas por país para manejo de contexto
"""
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from taller.middleware.country_url_migration import get_current_country_from_request


class CountryBaseView(TemplateView):
    """Vista base para manejo de contexto por país"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_country'] = get_current_country_from_request(self.request)
        context['country_name'] = self.get_country_name()
        context['language'] = self.get_country_language()
        return context
    
    def get_country_name(self):
        """Override en subclases"""
        return "País"
    
    def get_country_language(self):
        """Override en subclases"""
        return "es"


class ChileHomeView(CountryBaseView):
    """Vista principal para Chile"""
    template_name = 'dashboard_chile.html'
    
    def get_country_name(self):
        return "Chile"
    
    def get_country_language(self):
        return "es"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'eGarage Chile - Dashboard',
            'welcome_message': 'Bienvenido a eGarage Chile',
            'currency': 'CLP',
            'currency_symbol': '$',
        })
        return context


class USAHomeView(CountryBaseView):
    """Vista principal para USA"""
    template_name = 'dashboard_usa.html'
    
    def get_country_name(self):
        return "United States"
    
    def get_country_language(self):
        return "en"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'eGarage USA - Dashboard',
            'welcome_message': 'Welcome to eGarage USA',
            'currency': 'USD',
            'currency_symbol': '$',
        })
        return context


# Views simples por país
def dashboard_cl_view(request):
    """Dashboard profesional para Chile - Redirige al Centro de Operaciones Espacial si está autenticado"""
    
    # Si el usuario está autenticado, redirigir al Centro de Operaciones Espacial
    if request.user.is_authenticated:
        try:
            # Verificar que tenga empresa asociada
            empresa = request.user.empresa
            # Detectar país y redirigir a la ruta correcta
            from django.shortcuts import redirect
            if hasattr(request.user, 'pais') and request.user.pais == 'US':
                return redirect('/us/centro-operaciones-espacial/')
            else:
                return redirect('/cl/centro-operaciones-espacial/')
        except:
            # Si no tiene empresa, crear una básica
            from taller.models.empresa import Empresa
            empresa, created = Empresa.objects.get_or_create(
                user=request.user,
                defaults={'nombre_taller': f'Taller de {request.user.username}'}
            )
            from django.shortcuts import redirect
            if hasattr(request.user, 'pais') and request.user.pais == 'US':
                return redirect('/us/centro-operaciones-espacial/')
            else:
                return redirect('/cl/centro-operaciones-espacial/')
    
    # Si no está autenticado, mostrar página de bienvenida
    context = {
        'current_country': 'CL',
        'country_name': 'Chile',
        'language': 'es',
        'page_title': 'eGarage Chile - Gestión Automotriz Profesional',
        'welcome_message': 'Bienvenido a eGarage Chile',
        'currency': 'CLP',
        'currency_symbol': '$',
    }
    return render(request, 'onboarding/bienvenida_chile.html', context)


def dashboard_us_view(request):
    """Dashboard simple para USA"""
    context = {
        'current_country': 'US', 
        'country_name': 'United States',
        'language': 'en',
        'page_title': 'eGarage USA - Professional Workshop Management',
        'welcome_message': 'Welcome to eGarage USA',
        'currency': 'USD',
        'currency_symbol': '$',
    }
    return render(request, 'dashboard_usa.html', context)


# Views de test por país
def test_chile_view(request):
    """Endpoint de test para Chile"""
    return JsonResponse({
        'status': 'success',
        'country': 'CL',
        'message': 'Test Chile funcionando correctamente',
        'timestamp': str(timezone.now()),
    })


def test_usa_view(request):
    """Endpoint de test para USA"""
    return JsonResponse({
        'status': 'success',
        'country': 'US',
        'message': 'Test USA working correctly',
        'timestamp': str(timezone.now()),
    })


# API endpoints de país
def api_country_info(request):
    """API que retorna información del país actual"""
    country = get_current_country_from_request(request)
    
    country_info = {
        'CL': {
            'name': 'Chile',
            'language': 'es',
            'currency': 'CLP',
            'timezone': 'America/Santiago',
            'phone_code': '+56',
        },
        'US': {
            'name': 'United States',
            'language': 'en', 
            'currency': 'USD',
            'timezone': 'America/New_York',
            'phone_code': '+1',
        }
    }
    
    return JsonResponse({
        'country_code': country,
        'country_info': country_info.get(country, {}),
        'detected_from': 'url_prefix',
    })


# Import timezone
from django.utils import timezone
