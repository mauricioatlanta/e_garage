from dal import autocomplete

from django.db.models import Q

from taller.models.clientes import Cliente
from taller.models.repuesto import Repuesto
from taller.models.vehiculos import Vehiculo


class RepuestoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Repuesto.objects.none()

        # BLINDAJE MULTI-TENANT: Usar request.user.empresa directamente
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return Repuesto.objects.none()

        qs = Repuesto.objects.filter(empresa=empresa)

        if self.q:
            qs = qs.filter(
                Q(part_number__icontains=self.q) | Q(nombre__icontains=self.q)
            )
        return qs.order_by("nombre")


class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Vehiculo.objects.none()

        # BLINDAJE MULTI-TENANT: Usar request.user.empresa directamente
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return Vehiculo.objects.none()

        cliente_id = self.forwarded.get("cliente")
        qs = Vehiculo.objects.filter(cliente__empresa=empresa)

        # Filtrar por cliente si se proporciona
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)

        if self.q:
            qs = qs.filter(Q(patente__icontains=self.q) | Q(vin__icontains=self.q))

        return qs.order_by("patente")


class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()

        # BLINDAJE MULTI-TENANT: Usar request.user.empresa directamente
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return Cliente.objects.none()

        qs = Cliente.objects.filter(empresa=empresa)

        if self.q:
            qs = qs.filter(
                Q(nombre__icontains=self.q)
                | Q(apellido__icontains=self.q)
                | Q(email__icontains=self.q)
                | Q(telefono__icontains=self.q)
                | Q(tax_id__icontains=self.q)
            )

        return qs.order_by("nombre")


class ServicioAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            from taller.servicios.models import Servicio

            return Servicio.objects.none()

        from taller.servicios.models import Servicio

        # BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa del usuario
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return Servicio.objects.none()

        # Verificar si Servicio tiene campo empresa
        if hasattr(Servicio, "empresa"):
            qs = Servicio.objects.filter(empresa=empresa)
        else:
            # Si Servicio no es multi-tenant, usar todos pero filtrar por categoria si corresponde
            qs = Servicio.objects.all()

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return qs.order_by("nombre")
