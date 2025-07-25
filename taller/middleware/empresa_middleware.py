# Middleware que añade la empresa al request según el usuario logueado
from django.shortcuts import redirect
from django.urls import reverse
from taller.models.empresa import Empresa

class EmpresaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                request.empresa = request.user.empresa
                
                # Verificar si la suscripción está vencida
                if request.empresa.debe_bloquear and not self.is_exempt_url(request.path):
                    return redirect('suspension')
                    
            except Empresa.DoesNotExist:
                request.empresa = None
        else:
            request.empresa = None
            
        return self.get_response(request)
    
    def is_exempt_url(self, path):
        """URLs que no requieren suscripción activa"""
        exempt_urls = [
            '/suspension/',
            '/accounts/logout/',
            '/admin/',
            '/static/',
            '/media/',
            '/comprobante-pago/',
        ]
        return any(path.startswith(url) for url in exempt_urls)
