"""
Middleware para resolver la empresa activa y su país de forma consistente.
"""

from django.utils.deprecation import MiddlewareMixin

from taller.models import Empresa


class CompanyCountryMiddleware(MiddlewareMixin):
    """
    Resuelve la empresa activa y su país de forma consistente.
    Prioridad:
    1) empresa_id en sesión
    2) empresa del usuario (user.empresa)
    3) None
    Guarda:
      request.company, request.country ('US'/'CL')
    """

    def process_request(self, request):
        company = None
        company_id = request.session.get("empresa_id")

        if company_id:
            try:
                company = (
                    Empresa.objects.select_related(None)
                    .only("id", "pais", "nombre_taller")
                    .get(id=company_id)
                )
            except Empresa.DoesNotExist:
                company = None

        if not company and request.user.is_authenticated:
            try:
                company = Empresa.objects.get(user=request.user)
            except Empresa.DoesNotExist:
                company = None

        request.company = company

        # NO sobrescribir request.country si ya fue establecido por CountryContextMiddleware
        # El CountryContextMiddleware maneja la lógica de redirección automática
        if not hasattr(request, "country"):
            # Solo establecer país si no fue establecido por middleware anterior
            if request.path.startswith("/us/"):
                request.country = "US"
            elif request.path.startswith("/cl/"):
                request.country = "CL"
            else:
                # PRIORIDAD: País desde empresa del usuario
                request.country = getattr(company, "pais", None) or "CL"

        # Debug opcional (remover en producción)
        if hasattr(request, "user") and request.user.is_authenticated:
            print(f"MIDDLEWARE - Usuario: {request.user.username}")
            print(
                f"MIDDLEWARE - Empresa: {getattr(company, 'nombre_taller', 'None')} (ID: {getattr(company, 'id', 'None')})"
            )
            print(f"MIDDLEWARE - País: {request.country}")
