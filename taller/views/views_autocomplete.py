from dal import autocomplete
from django.db.models import Q
from taller.models.repuesto import Repuesto
from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente

class RepuestoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Repuesto.objects.none()

        from taller.models.perfilusuario import PerfilUsuario
        try:
            perfil = PerfilUsuario.objects.get(user=self.request.user)
            if perfil.es_superadmin:
                qs = Repuesto.objects.all()
            else:
                qs = Repuesto.objects.filter(empresa=perfil.empresa)
        except PerfilUsuario.DoesNotExist:
            qs = Repuesto.objects.none()
            
        if self.q:
            qs = qs.filter(Q(part_number__icontains=self.q) | Q(nombre__icontains=self.q))
        return qs.order_by('nombre')

class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Vehiculo.objects.none()

        from taller.models.perfilusuario import PerfilUsuario
        try:
            perfil = PerfilUsuario.objects.get(user=self.request.user)
            cliente_id = self.forwarded.get('cliente')
            
            if perfil.es_superadmin:
                qs = Vehiculo.objects.all()
            else:
                qs = Vehiculo.objects.filter(cliente__empresa=perfil.empresa)
                
            # Filtrar por cliente si se proporciona
            if cliente_id:
                qs = qs.filter(cliente_id=cliente_id)
                
        except PerfilUsuario.DoesNotExist:
            qs = Vehiculo.objects.none()
            
        if self.q:
            qs = qs.filter(Q(patente__icontains=self.q) | Q(vin__icontains=self.q))
            
        return qs.order_by('patente')

class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()

        from taller.models.perfilusuario import PerfilUsuario
        try:
            perfil = PerfilUsuario.objects.get(user=self.request.user)
            if perfil.es_superadmin:
                qs = Cliente.objects.all()
            else:
                qs = Cliente.objects.filter(empresa=perfil.empresa)
        except PerfilUsuario.DoesNotExist:
            qs = Cliente.objects.none()

        if self.q:
            qs = qs.filter(
                Q(nombre__icontains=self.q) |
                Q(rut__icontains=self.q) |
                Q(email__icontains=self.q) |
                Q(telefono__icontains=self.q)
            )

        return qs.order_by('nombre')

class ServicioAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            from taller.servicios.models import Servicio
            return Servicio.objects.none()

        from taller.servicios.models import Servicio
        qs = Servicio.objects.all()
        
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return qs.order_by('nombre')
