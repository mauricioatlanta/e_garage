# taller/views_autocomplete.py
from dal import autocomplete

from django.db.models import Q

from taller.models.clientes import Cliente
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo


# -----------------------
# Helpers
# -----------------------
def _get_empresa(request):
    """
    Obtiene la empresa activa del request de forma robusta.
    """
    # Si tienes middleware que inyecta request.empresa, úsalo:
    emp = getattr(request, "empresa", None)
    if emp:
        return emp

    # Fallback: user.empresa
    user_emp = getattr(getattr(request, "user", None), "empresa", None)
    if user_emp:
        return user_emp

    # Último recurso: util existente (si lo usas en tu proyecto)
    try:
        from taller.utils.empresa import get_or_create_empresa

        return get_or_create_empresa(request)
    except Exception:
        return None


def _resolve_country_from_request(request):
    # 1) empresa en request
    emp = _get_empresa(request)
    pais = getattr(emp, "pais", None)
    if pais in ("CL", "US"):
        return pais

    # 2) prefijo URL
    path = (request.path or "").lower()
    if path.startswith("/cl/"):
        return "CL"
    if path.startswith("/us/"):
        return "US"
    return None


# -----------------------
# Técnicos
# -----------------------
class TecnicoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Tecnico.objects.none()

        empresa = _get_empresa(self.request)
        qs = Tecnico.objects.all()
        # Si Técnicos deben ser por empresa, descomenta:
        # qs = qs.filter(empresa=empresa)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs

    # IMPORTANTE: para FKs devuelve el PK, no el nombre
    def get_result_value(self, result):
        return result.pk

    def get_result_label(self, result):
        return result.nombre


# -----------------------
# Clientes
# -----------------------
class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()

        empresa = _get_empresa(self.request)
        if not empresa:
            return Cliente.objects.none()

        qs = Cliente.objects.filter(empresa=empresa)
        
        # Obtener el término de búsqueda
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(apellido__icontains=q)
                | Q(email__icontains=q)
                | Q(telefono__icontains=q)
            )
        return qs.order_by("nombre", "apellido")

    def get_result_label(self, result):
        tel = result.telefono or "Sin teléfono"
        # Muestra: "Nombre Apellido - Teléfono"
        return f"{result.nombre} {result.apellido} - {tel}"


# -----------------------
# Vehículos (filtra por empresa y por cliente via forward)
# -----------------------
class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Vehiculo.objects.none()

        empresa = _get_empresa(self.request)
        if not empresa:
            return Vehiculo.objects.none()

        qs = Vehiculo.objects.select_related("cliente", "marca", "modelo").filter(
            empresa=empresa
        )

        # Soporta forward de DAL y querystring plano
        cliente_id = self.forwarded.get("cliente") or self.request.GET.get("cliente")
        if cliente_id:
            try:
                cliente_id = int(cliente_id)
                qs = qs.filter(cliente_id=cliente_id, cliente__empresa=empresa)
            except (TypeError, ValueError):
                return Vehiculo.objects.none()

        # Obtener el término de búsqueda
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(patente__icontains=q)
                | Q(modelo__nombre__icontains=q)
                | Q(marca__nombre__icontains=q)
                | Q(vin__icontains=q)
            )

        return qs.order_by("patente")

    def get_result_label(self, result):
        # Evita coma al final (tupla) -> SOLO string
        marca = getattr(result.marca, "nombre", None) or "Sin marca"
        modelo = getattr(result.modelo, "nombre", None) or "Sin modelo"
        base = f"{result.patente or 'Sin patente'} - {marca} {modelo}"
        # Puedes agregar VIN si existe
        if getattr(result, "vin", None):
            base += f" (VIN {result.vin})"
        return base


# -----------------------
# Marca / Modelo (country-aware)
# -----------------------
class MarcaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Marca.objects.none()

        country = _resolve_country_from_request(self.request)
        if country not in ("CL", "US"):
            return Marca.objects.none()

        qs = Marca.objects.filter(country=country)
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs.order_by("nombre")


class ModeloAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Modelo.objects.none()

        country = _resolve_country_from_request(self.request)
        if country not in ("CL", "US"):
            return Modelo.objects.none()

        qs = Modelo.objects.select_related("marca").filter(country=country)

        # forward desde DAL
        marca_id = self.forwarded.get("marca")
        if marca_id:
            qs = qs.filter(marca_id=marca_id)

        # fallback desde querystring (si lo usas por fetch manual)
        marca_id_qs = self.request.GET.get("marca")
        if marca_id_qs:
            qs = qs.filter(marca_id=marca_id_qs)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs.order_by("nombre")

    def get_result_label(self, result):
        return result.nombre


# -----------------------
# Repuestos
# -----------------------
class RepuestoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Repuesto.objects.none()

        empresa = _get_empresa(self.request)
        if not empresa:
            return Repuesto.objects.none()

        qs = Repuesto.objects.filter(empresa=empresa)

        if self.q:
            qs = qs.filter(
                Q(part_number__icontains=self.q) | Q(nombre__icontains=self.q)
            )
        return qs.order_by("nombre")

    def get_result_label(self, result):
        precio = getattr(result, "precio_venta", None) or getattr(
            result, "precio", None
        )
        if precio:
            return f"{result.part_number} - {result.nombre} (${precio})"
        return f"{result.part_number} - {result.nombre}"


# -----------------------
# Servicios
# -----------------------
class ServicioAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            from taller.servicios.models import Servicio

            return Servicio.objects.none()

        from taller.servicios.models import Servicio

        empresa = _get_empresa(self.request)
        if not empresa:
            return Servicio.objects.none()

        # Verificar si Servicio tiene campo empresa
        if hasattr(Servicio, "empresa"):
            qs = Servicio.objects.filter(empresa=empresa)
        else:
            # Si Servicio no es multi-tenant, usar todos
            qs = Servicio.objects.all()

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return qs.order_by("nombre")

    def get_result_label(self, result):
        precio = getattr(result, "precio", None)
        if precio:
            return f"{result.nombre} (${precio})"
        return result.nombre
