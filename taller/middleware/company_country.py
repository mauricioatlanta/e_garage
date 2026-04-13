"""
Middleware para resolver la empresa activa y su país de forma consistente.
"""

from django.utils.deprecation import MiddlewareMixin


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
        from django.apps import apps

        Empresa = apps.get_model("taller", "Empresa")

        company = None
        company_id = None

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

        # Preserve an existing request.country set by earlier middleware.
        if not hasattr(request, "country"):
            path = request.path or ""
            request.country = None

            for prefix, country in {
                "/cl/": "CL",
                "/us/": "US",
                "/br/": "BR",
                "/mx/": "MX",
                "/ar/": "AR",
                "/pe/": "PE",
                "/co/": "CO",
                "/ec/": "EC",
                "/ve/": "VE",
                "/uy/": "UY",
            }.items():
                if path.startswith(prefix):
                    request.country = country
                    break

            if request.country is None:
                request.country = (getattr(company, "pais", None) or "CL").upper()

        # Debug opcional (remover en producción)
        if hasattr(request, "user") and request.user.is_authenticated:
            print(f"MIDDLEWARE - Usuario: {request.user.username}")
            print(
                f"MIDDLEWARE - Empresa: {getattr(company, 'nombre_taller', 'None')} (ID: {getattr(company, 'id', 'None')})"
            )
            print(f"MIDDLEWARE - País: {request.country}")
