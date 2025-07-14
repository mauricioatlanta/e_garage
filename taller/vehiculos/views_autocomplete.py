from dal import autocomplete
from taller.models.vehiculos import Vehiculo

class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Vehiculo.objects.all()
        # Log para depuración: ver qué llega como forwarded
        import logging
        logger = logging.getLogger('django')
        logger.info(f"[DAL] forwarded: {self.forwarded}")
        cliente_id = self.forwarded.get('cliente', None)
        logger.info(f"[DAL] cliente_id recibido: {cliente_id}")
        if cliente_id:
            try:
                cliente_id_int = int(cliente_id)
                qs = qs.filter(cliente_id=cliente_id_int)
                logger.info(f"[DAL] queryset filtrado por cliente_id={cliente_id_int}: {[v.patente for v in qs]}")
            except (ValueError, TypeError):
                logger.warning(f"[DAL] cliente_id no es un entero válido: {cliente_id}")
        if self.q:
            qs = qs.filter(patente__icontains=self.q)
        return qs
