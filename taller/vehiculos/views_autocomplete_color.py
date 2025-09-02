from dal import autocomplete
from taller.models.extras_vehiculo import ColorVehiculo

class ColorVehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # CORREGIDO: Filtrar colores por país del usuario
        user = self.request.user
        if hasattr(user, 'empresa') and user.empresa and hasattr(user.empresa, 'pais'):
            pais = user.empresa.pais
            qs = ColorVehiculo.get_colores_para_pais(pais)
        else:
            qs = ColorVehiculo.get_colores_para_pais('CL')  # Default a Chile
            
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs
