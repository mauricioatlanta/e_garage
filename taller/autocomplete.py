# taller/autocomplete/views.py
from dal import autocomplete

from django.db.models import Q

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo


def _vehicle_autocomplete_label(result):
    anio = getattr(result, "anio", "") or ""
    marca = (
        getattr(result, "marca_texto", "")
        or getattr(getattr(result, "marca", None), "nombre", "")
        or ""
    )
    modelo = (
        getattr(result, "modelo_texto", "")
        or getattr(getattr(result, "modelo", None), "nombre", "")
        or ""
    )
    patente = getattr(result, "patente", "") or getattr(result, "placa", "") or ""
    fallback = patente or getattr(result, "vin", "") or ""

    parts = [
        str(anio).strip() if anio else "",
        str(marca).strip(),
        str(modelo).strip(),
        str(fallback).strip(),
    ]
    return " - ".join(part for part in parts if part) or f"Vehículo #{result.pk}"


class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()
        qs = Cliente.objects.filter(empresa=self.request.empresa)
        q = self.q or ""
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(tax_id__icontains=q) | Q(email__icontains=q))
        return qs.order_by("nombre")


class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Vehiculo.objects.none()
        # Solo vehículos de cliente (para documentos)
        qs = Vehiculo.objects.filter(empresa=self.request.empresa).select_related(
            "marca", "modelo"
        )
        # Filtro por cliente desde forward
        cli_id = self.forwarded.get("cliente")
        if cli_id:
            qs = qs.filter(cliente_id=cli_id)
        # Búsqueda por patente/VIN/marca/modelo
        q = self.q or ""
        if q:
            qs = qs.filter(
                Q(patente__icontains=q)
                | Q(vin__icontains=q)
                | Q(modelo__nombre__icontains=q)
                | Q(marca__nombre__icontains=q)
            )
        return qs.order_by("-id")

    def get_result_label(self, result):
        return _vehicle_autocomplete_label(result)

    def get_selected_result_label(self, result):
        return _vehicle_autocomplete_label(result)
