
from dal import autocomplete
from django.db.models import Q
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.mecanico import Mecanico

class MecanicoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Los mecánicos pueden ser globales o podríamos filtrarlos por empresa si se requiere
        qs = Mecanico.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs

    def create(self, text):
        # Permitir crear un nuevo mecánico desde el widget select2 (soporte oficial DAL)
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
            empresa = self.request.user.empresa_usuario
        except AttributeError:
            # Si no tiene empresa asociada, buscar o crear una
            from taller.models.empresa import Empresa
            empresa, created = Empresa.objects.get_or_create(
                usuario=self.request.user,
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
            empresa = self.request.user.empresa_usuario
        except AttributeError:
            # Si no tiene empresa asociada, buscar o crear una
            from taller.models.empresa import Empresa
            empresa, created = Empresa.objects.get_or_create(
                usuario=self.request.user,
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


# --- AUTOCOMPLETE PARA MARCA ---
class MarcaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Marca.objects.none()

        qs = Marca.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs.order_by('nombre')


# --- AUTOCOMPLETE PARA MODELO ---
class ModeloAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Modelo.objects.none()

        qs = Modelo.objects.select_related('marca')
        marca_id = self.forwarded.get('marca')
        if marca_id:
            qs = qs.filter(marca_id=marca_id)
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs.order_by('nombre')
