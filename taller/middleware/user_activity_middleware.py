import logging
from taller.models.user_activity_log import UserActivityLog

logger = logging.getLogger(__name__)

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            path = request.path or ""
            
            # Omitir archivos estáticos, librerías, workers y la propia vista de analytics
            ignorar = ("/static/", "/media/", "/jsi18n/", "/service-worker.js", "/analytics/", "/favicon.ico")
            if not any(path.startswith(prefix) for prefix in ignorar):
                
                # Obtener la empresa asociada de forma segura
                empresa = getattr(request, "empresa_actual", None)
                if not empresa and hasattr(user, "perfilusuario"):
                    empresa = getattr(user.perfilusuario, "empresa", None)
                if not empresa and hasattr(user, "empresa"):
                    try:
                        empresa = user.empresa
                    except Exception:
                        empresa = None

                ip = request.META.get("HTTP_X_FORWARDED_FOR")
                if ip:
                    ip = ip.split(",")[0].strip()
                else:
                    ip = request.META.get("REMOTE_ADDR")

                try:
                    UserActivityLog.objects.create(
                        user=user,
                        empresa=empresa,
                        path=path[:255],
                        method=request.method,
                        ip_address=ip
                    )
                except Exception as e:
                    logger.warning("No se pudo registrar UserActivityLog: %s", e)

        return response
