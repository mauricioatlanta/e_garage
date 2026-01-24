"""
Middleware para forzar ALLOWED_HOSTS correcto
Se ejecuta antes de CommonMiddleware para evitar errores de DisallowedHost
"""


class FixAllowedHostsMiddleware:
    """
    Middleware que fuerza ALLOWED_HOSTS antes de que CommonMiddleware valide el host.
    Debe estar ANTES de django.middleware.common.CommonMiddleware en MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Forzar ALLOWED_HOSTS al inicializar el middleware
        from django.conf import settings
        correct_hosts = ["127.0.0.1", "localhost", "159.223.200.106", "egarage.cl", "www.egarage.cl"]
        if settings.ALLOWED_HOSTS == ['*'] or 'egarage.cl' not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS = correct_hosts

    def __call__(self, request):
        # También verificar en cada request por si acaso
        from django.conf import settings
        if 'egarage.cl' not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "159.223.200.106", "egarage.cl", "www.egarage.cl"]
        
        response = self.get_response(request)
        return response
