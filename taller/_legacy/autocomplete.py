# taller/autocomplete/views.py
from dal import autocomplete

from django.db.models import Q

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo


class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()
        qs = Cliente.objects.filter(empresa=self.request.user.empresa)
        q = self.q or ""
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(tax_id__icontains=q) | Q(email__icontains=q))
        return qs.order_by("nombre")


class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Vehiculo.objects.none()
        qs = Vehiculo.objects.filter(empresa=self.request.user.empresa)
        # Filtro por cliente desde forward
        cli_id = self.forwarded.get("cliente")
        if cli_id:
            qs = qs.filter(cliente_id=cli_id)
        # Búsqueda por patente/VIN/marca/modelo
        q = self.q or ""
        if q:
            qs = qs.filter(
                Q(patente__icontains=q)
                | Q(vin__icontains=q)
                | Q(modelo__nombre__icontains=q)
                | Q(marca__nombre__icontains=q)
            )
        return qs.order_by("-id")
