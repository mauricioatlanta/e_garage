from dal import autocomplete
from taller.models.extras_vehiculo import CajaVehiculo

class CajaVehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = CajaVehiculo.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs
