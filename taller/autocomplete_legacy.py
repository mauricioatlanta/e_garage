from dal import autocomplete

from django.db.models import Q

from taller.models.clientes import Cliente
from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo


class MotorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = MotorVehiculo.objects.all()

        # Filtrar por modelo si se proporciona
        modelo_id = self.forwarded.get("modelo", None)

        # También verificar si viene como parámetro GET directo
        if not modelo_id:
            modelo_id = self.request.GET.get("modelo")

        if modelo_id:
            try:
                modelo = Modelo.objects.get(id=modelo_id)
                # Filtrar motores que están asociados a este modelo
                qs = qs.filter(modelos__id=modelo_id)
            except Modelo.DoesNotExist:
                qs = qs.none()
        else:
            # Si no hay modelo seleccionado, no mostrar motores
            qs = qs.none()

        if self.q:
            qs = qs.filter(Q(nombre__icontains=self.q))

        return qs.order_by("nombre")


class CajaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = CajaVehiculo.objects.all()

        # Filtrar por modelo si se proporciona
        modelo_id = self.forwarded.get("modelo", None)

        # También verificar si viene como parámetro GET directo
        if not modelo_id:
            modelo_id = self.request.GET.get("modelo")

        if modelo_id:
            try:
                modelo = Modelo.objects.get(id=modelo_id)
                # Filtrar cajas que están asociadas a este modelo
                qs = qs.filter(modelos__id=modelo_id)
            except Modelo.DoesNotExist:
                qs = qs.none()
        else:
            # Si no hay modelo seleccionado, no mostrar cajas
            qs = qs.none()

        if self.q:
            qs = qs.filter(Q(nombre__icontains=self.q))

        return qs.order_by("nombre")


class ModeloAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Modelo.objects.all()

        # Filtrar por marca si se proporciona
        marca_id = self.forwarded.get("marca", None)
        if marca_id:
            qs = qs.filter(marca__id=marca_id)

        # También verificar si viene como parámetro GET directo
        if not marca_id:
            marca_id = self.request.GET.get("marca")
            if marca_id:
                qs = qs.filter(marca__id=marca_id)

        if self.q:
            qs = qs.filter(Q(nombre__icontains=self.q))

        return qs.order_by("nombre")

    def get_result_label(self, result):
        """Personalizar la etiqueta mostrada para mostrar solo el nombre del modelo"""
        return result.nombre


class MarcaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Marca.objects.all()

        if self.q:
            qs = qs.filter(Q(nombre__icontains=self.q))

        return qs.order_by("nombre")


class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Cliente.objects.all()

        # Filtrar por empresa si está disponible
        if self.request.empresa:
            qs = qs.filter(empresa=self.request.empresa)

        if self.q:
            qs = qs.filter(Q(nombre__icontains=self.q) | Q(apellido__icontains=self.q))

        return qs.order_by("nombre", "apellido")
