from dal import autocomplete
from taller.models.extras_vehiculo import MotorVehiculo

class MotorVehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = MotorVehiculo.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        modelo_id = self.forwarded.get('modelo', None)
        if modelo_id:
            qs = qs.filter(modelo_id=modelo_id)
        return qs
