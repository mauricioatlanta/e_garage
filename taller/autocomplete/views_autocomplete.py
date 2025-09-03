
from dal import autocomplete
from django.db.models import Q
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.tecnico import Tecnico

class TecnicoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Los técnicos pueden ser globales o podríamos filtrarlos por empresa si se requiere
        qs = Tecnico.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs

    def create(self, text):
        # Permitir crear un nuevo técnico desde el widget select2 (soporte oficial DAL)
        return self.get_queryset().model.objects.create(nombre=text)
    
    def get_result_label(self, result):
        # Para CharField, devolver el nombre en lugar del ID
        return result.nombre
    
    def get_result_value(self, result):
        # Para CharField, devolver el nombre en lugar del ID
        return result.nombre


class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Filtrar por empresa del usuario autenticado
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()
            
        try:
            empresa = self.request.user.empresa
        except AttributeError:
            # Si no tiene empresa asociada, buscar o crear una
            from taller.models.empresa import Empresa
            empresa, created = Empresa.objects.get_or_create(
                user=self.request.user,
                defaults={'nombre_taller': f'Taller de {self.request.user.username}'}
            )
        
        qs = Cliente.objects.filter(empresa=empresa)
        if self.q:
            qs = qs.filter(
                Q(nombre__icontains=self.q) |
                Q(apellido__icontains=self.q) |
                Q(email__icontains=self.q) |
                Q(telefono__icontains=self.q)
            )
        return qs

    def get_result_label(self, result):
        telefono = result.telefono or 'Sin teléfono'
        return f"{result.nombre} {result.apellido} - {telefono}"


class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Vehiculo.objects.none()

        # Obtener empresa del usuario
        try:
            empresa = self.request.user.empresa
        except AttributeError:
            # Si no tiene empresa asociada, buscar o crear una
            from taller.models.empresa import Empresa
            empresa, created = Empresa.objects.get_or_create(
                user=self.request.user,
                defaults={'nombre_taller': f'Taller de {self.request.user.username}'}
            )

        # Filtrar vehículos por empresa (a través del cliente)
        qs = Vehiculo.objects.select_related('cliente').filter(empresa=empresa)

        # Filtrar por cliente específico si se proporciona
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            # Verificar que el cliente pertenece a la empresa del usuario
            try:
                cliente = Cliente.objects.get(id=cliente_id, empresa=empresa)
                qs = qs.filter(cliente=cliente)
            except Cliente.DoesNotExist:
                # Cliente no existe o no pertenece a la empresa
                return Vehiculo.objects.none()

        if self.q:
            qs = qs.filter(
                Q(patente__icontains=self.q) |
                Q(modelo__nombre__icontains=self.q)
            )

        return qs.order_by('patente')


def _resolve_country_from_request(request):
    """
    Resolución robusta del país:
    1) middleware: request.empresa.pais (CL/US)
    2) perfil: request.user.empresa.pais
    3) sesión: empresa_actual_id → Empresa.pais (si la usas)
    4) prefijo de la URL: '/us/' o '/cl/' como último recurso
    """
    # 1) middleware
    empresa = getattr(request, "empresa", None)
    pais = getattr(empresa, "pais", None)
    if pais in ("CL", "US"):
        return pais

    # 2) perfil
    user_emp = getattr(getattr(request, "user", None), "empresa", None)
    pais = getattr(user_emp, "pais", None)
    if pais in ("CL", "US"):
        return pais

    # 3) sesión (opcional, si usas empresa_actual_id en session)
    empresa_id = request.session.get("empresa_actual_id")
    if empresa_id:
        from taller.models.empresa import Empresa
        try:
            e = Empresa.objects.only("pais").get(id=empresa_id)
            if e.pais in ("CL", "US"):
                return e.pais
        except Empresa.DoesNotExist:
            pass

    # 4) prefijo URL
    path = request.path.lower()
    if path.startswith("/us/"):
        return "US"
    if path.startswith("/cl/"):
        return "CL"

    return None


# --- AUTOCOMPLETE PARA MARCA ---
class MarcaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Marca.objects.none()

        country = _resolve_country_from_request(self.request)
        if country not in ("CL", "US"):
            # Falla cerrada: si no sabemos el país, no mostramos nada
            return Marca.objects.none()

        qs = Marca.objects.filter(country=country)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs.order_by("nombre")


# --- AUTOCOMPLETE PARA MODELO ---
class ModeloAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Modelo.objects.none()

        country = _resolve_country_from_request(self.request)
        if country not in ("CL", "US"):
            return Modelo.objects.none()

        qs = Modelo.objects.select_related('marca').filter(country=country)

        # Si llega marca desde forward de Select2, respétala
        marca_id = self.forwarded.get("marca")
        if marca_id:
            qs = qs.filter(marca_id=marca_id)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs.order_by("nombre")
