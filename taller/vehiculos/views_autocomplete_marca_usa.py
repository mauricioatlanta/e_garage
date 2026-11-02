from dal import autocomplete

from taller.models.marcas_usa import MarcaVehiculo


class MarcaVehiculoUSA_Autocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = MarcaVehiculo.objects.filter(pais_origen="USA", activa=True).order_by("nombre")
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        else:
            qs = qs[:50]  # Devuelve top 50 si no hay búsqueda
        return qs
