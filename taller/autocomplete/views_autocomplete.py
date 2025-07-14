
from dal import autocomplete
from django.db.models import Q
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo

from taller.models.mecanico import Mecanico
class MecanicoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Mecanico.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs

    def create(self, text):
        # Permitir crear un nuevo mecánico desde el widget select2 (soporte oficial DAL)
        return self.get_queryset().model.objects.create(nombre=text)


class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Cliente.objects.all()
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

        qs = Vehiculo.objects.select_related('cliente')

        # 👇 Este es el cambio: obtenemos directamente desde GET
        cliente_id = self.request.GET.get('cliente')

        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)

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
