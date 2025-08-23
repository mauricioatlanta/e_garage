from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login
from allauth.account.views import LoginView
from allauth.account import app_settings
from django.http import HttpResponseRedirect
import re

class CountryAwareLoginView(LoginView):
    """
    Vista de login que detecta el país desde el parámetro 'next'
    para asegurar el contexto correcto de país
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Detectar país desde next parameter si está disponible
        next_url = request.GET.get('next', '')
        if next_url:
            if next_url.startswith('/us/'):
                request.country = 'US'
                request.country_code = 'US'
            elif next_url.startswith('/cl/'):
                request.country = 'CL'
                request.country_code = 'CL'
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Asegurar que el contexto de país está disponible
        next_url = self.request.GET.get('next', '')
        if next_url.startswith('/us/'):
            context['country'] = 'US'
            context['current_country'] = 'usa'
        elif next_url.startswith('/cl/'):
            context['country'] = 'CL'  
            context['current_country'] = 'chile'
        else:
            # Por defecto Chile
            context['country'] = 'CL'
            context['current_country'] = 'chile'
            
        return context

# Vista funcional como alternativa
def country_aware_login(request):
    """
    Vista funcional de login que detecta país desde 'next' parameter
    """
    next_url = request.GET.get('next', '')
    
    # Detectar país desde next parameter
    if next_url.startswith('/us/'):
        request.country = 'US'
        request.country_code = 'US'
    elif next_url.startswith('/cl/'):
        request.country = 'CL'
        request.country_code = 'CL'
    else:
        # Por defecto Chile si no hay next o no tiene prefijo
        request.country = 'CL'
        request.country_code = 'CL'
    
    # Usar la vista original de allauth con contexto corregido
    from allauth.account.views import login as allauth_login
    return allauth_login(request)
