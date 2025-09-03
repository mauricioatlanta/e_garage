from dal import autocomplete
from django.utils.functional import cached_property
from taller.models.marca import Marca
from taller.models.modelo import Modelo

def _resolve_country_from_request(request):
    # 1) middleware: request.empresa.pais
    empresa = getattr(request, "empresa", None)
    pais = getattr(empresa, "pais", None)
    if pais in ("CL", "US"):
        return pais
    # 2) perfil: request.user.empresa.pais
    user_emp = getattr(getattr(request, "user", None), "empresa", None)
    pais = getattr(user_emp, "pais", None)
    if pais in ("CL", "US"):
        return pais
    # 3) prefijo URL (seguro ante rutas /us/ o /cl/)
    path = (request.path or "").lower()
    if path.startswith("/us/"):
        return "US"
    if path.startswith("/cl/"):
        return "CL"
    return None

class MarcaAutocomplete(autocomplete.Select2QuerySetView):
    @cached_property
    def country(self):
        return _resolve_country_from_request(self.request)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Marca.objects.none()
        if self.country not in ("CL", "US"):
            return Marca.objects.none()
        qs = Marca.objects.filter(country=self.country)
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs.order_by("nombre")

class ModeloAutocomplete(autocomplete.Select2QuerySetView):
    @cached_property
    def country(self):
        return _resolve_country_from_request(self.request)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Modelo.objects.none()
        if self.country not in ("CL", "US"):
            return Modelo.objects.none()
        qs = Modelo.objects.filter(country=self.country)

        # respetar forward['marca']
        marca_id = self.forwarded.get("marca")
        if marca_id:
            qs = qs.filter(marca_id=marca_id)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs.order_by("nombre")
