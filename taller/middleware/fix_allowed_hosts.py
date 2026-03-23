"""
Middleware opcional que une hosts mínimos a ALLOWED_HOSTS.

NO está en la cadena MIDDLEWARE por defecto. La fuente de verdad debe ser
la configuración de entorno: DJANGO_ALLOWED_HOSTS en .env.prod (o variable
de entorno), incluyendo la IP del servidor si se permite acceso directo por IP.
Si se rehabilita, va antes de CommonMiddleware.
"""


class FixAllowedHostsMiddleware:
    """
    Middleware que asegura que ALLOWED_HOSTS incluya siempre los hosts mínimos
    (IP del servidor, dominios principales, localhost) sin sobrescribir el resto.
    Debe estar ANTES de django.middleware.common.CommonMiddleware en MIDDLEWARE.
    """

    REQUIRED_HOSTS = frozenset({
        "127.0.0.1",
        "localhost",
        "159.223.200.106",
        "egarage.cl",
        "www.egarage.cl",
    })

    def __init__(self, get_response):
        self.get_response = get_response
        from django.conf import settings

        settings.ALLOWED_HOSTS = list(set(settings.ALLOWED_HOSTS) | self.REQUIRED_HOSTS)

    def __call__(self, request):
        from django.conf import settings

        settings.ALLOWED_HOSTS = list(set(settings.ALLOWED_HOSTS) | self.REQUIRED_HOSTS)
        return self.get_response(request)
