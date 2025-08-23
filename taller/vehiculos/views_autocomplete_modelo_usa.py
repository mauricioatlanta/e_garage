from dal import autocomplete
from taller.models.marcas_usa import ModeloVehiculo

class ModeloVehiculoUSA_Autocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ModeloVehiculo.objects.none()
        qs = ModeloVehiculo.objects.select_related('marca')
        # El formulario USA usa campo 'marca_usa'; DAL forward debe coincidir
        marca_id = self.forwarded.get('marca_usa') or self.forwarded.get('marca')
        if marca_id:
            qs = qs.filter(marca_id=marca_id)
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        else:
            qs = qs[:50]  # Devuelve top 50 si no hay búsqueda
        return qs.order_by('nombre')
