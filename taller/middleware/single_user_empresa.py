"""
Middleware para restricción de usuario único por empresa
Asegura que solo el usuario principal de cada empresa pueda acceder al sistema
"""

from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth import logout
from taller.models.empresa import Empresa

class SingleUserPerEmpresaMiddleware:
    """
    Middleware que valida que solo un usuario por empresa pueda usar el sistema
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Rutas que no requieren validación
        self.exempt_paths = [
            '/admin/',
            '/accounts/',
            '/login/',
            '/logout/',
            '/registro/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Procesar antes de la vista
        if request.user.is_authenticated and not self.is_exempt_path(request.path):
            if not self.validate_user_empresa_access(request):
                logout(request)
                return render(request, 'suscripcion/usuario_existente.html')
        
        response = self.get_response(request)
        return response

    def is_exempt_path(self, path):
        """Verificar si la ruta está exenta de validación"""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def validate_user_empresa_access(self, request):
        """
        Validar que el usuario autenticado es el único usuario de su empresa
        """
        try:
            # Verificar que el usuario tiene una empresa asignada
            empresa = request.user.empresa
            
            # Verificar que es el único usuario de esta empresa
            # (Esta validación es redundante con el OneToOneField, pero es una doble verificación)
            if empresa.user != request.user:
                return False
                
            return True
            
        except Empresa.DoesNotExist:
            # El usuario no tiene empresa asignada
            return False
        except Exception:
            # Cualquier otro error, denegar acceso por seguridad
            return False
