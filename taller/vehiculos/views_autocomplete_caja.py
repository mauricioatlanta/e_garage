from dal import autocomplete

from taller.models.extras_vehiculo import CajaVehiculo


class CajaVehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = CajaVehiculo.objects.all()

        # Filtrar por modelo usando forward
        modelo_id = self.forwarded.get("modelo")
        if modelo_id:
            # Buscar cajas que estén asociadas a este modelo
            qs = qs.filter(modelos__id=modelo_id)
        else:
            # Si no hay modelo seleccionado, no mostrar cajas
            qs = qs.none()

        # Búsqueda por texto
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return qs
