from dal import autocomplete
from taller.models.vehiculos import Vehiculo

class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Vehiculo.objects.all()
        
        # Log para depuración
        import logging
        logger = logging.getLogger('django')
        logger.info(f"[DAL] forwarded: {self.forwarded}")
        logger.info(f"[DAL] GET params: {dict(self.request.GET)}")
        
        # Intentar obtener cliente_id tanto de forwarded como de GET
        cliente_id = self.forwarded.get('cliente', None) or self.request.GET.get('cliente')
        logger.info(f"[DAL] cliente_id recibido: {cliente_id}")
        
        if cliente_id:
            try:
                cliente_id_int = int(cliente_id)
                qs = qs.filter(cliente_id=cliente_id_int)
                logger.info(f"[DAL] queryset filtrado por cliente_id={cliente_id_int}: {[v.patente for v in qs]}")
            except (ValueError, TypeError):
                logger.warning(f"[DAL] cliente_id no es un entero válido: {cliente_id}")
        
        # Filtrar por término de búsqueda
        if self.q:
            qs = qs.filter(patente__icontains=self.q)
            
        return qs
    
    def get_result_label(self, result):
        """Personalizar cómo se muestra cada vehículo en los resultados"""
        marca = result.marca.nombre if result.marca else "Sin marca"
        modelo = result.modelo.nombre if result.modelo else "Sin modelo"
        return f"{result.patente} - {marca} {modelo}"
