from dal import autocomplete
from taller.models.extras_vehiculo import ColorVehiculo

class ColorVehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ColorVehiculo.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs
