# taller/views_autocomplete.py
from dal import autocomplete
from taller.models.vehiculos import Vehiculo



class AutocompleteVehiculo(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Vehiculo.objects.all()
        if self.q:
            qs = qs.filter(patente__icontains=self.q)
        return qs

