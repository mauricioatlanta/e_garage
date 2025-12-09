# taller/vehiculos/dal_views.py
from dal import autocomplete

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from taller.models.vehiculos import CajaVehiculo, Modelo, MotorVehiculo


class _EmpresaMixin:
    def _qs_empresa(self, qs):
        empresa = getattr(self.request.user, "empresa", None)
        return qs.filter(empresa=empresa) if empresa else qs.none()


class ModeloAutocomplete(LoginRequiredMixin, _EmpresaMixin, autocomplete.Select2QuerySetView):
    """Modelos del tenant filtrados por marca (forward='marca')."""

    def get_queryset(self):
        qs = self._qs_empresa(Modelo.objects.all())

        # Filtrar por marca si se pasa en forward
        marca_id = self.forwarded.get("marca")
        if marca_id:
            qs = qs.filter(marca_id=marca_id)

        q = (self.q or "").strip()
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs.order_by("nombre")

    # Solo mostrar el nombre del modelo
    def get_result_label(self, obj: Modelo):
        return getattr(obj, "nombre", "") or str(obj.pk)


class MotorPorModeloAutocomplete(
    LoginRequiredMixin, _EmpresaMixin, autocomplete.Select2QuerySetView
):
    """Motores del tenant filtrados por el modelo (forward='modelo')."""

    def get_queryset(self):
        qs = self._qs_empresa(MotorVehiculo.objects.all())

        modelo_id = self.forwarded.get("modelo")
        if modelo_id:
            # Filtrar por relación ManyToMany (MotorVehiculo/CajaVehiculo solo tienen 'modelos', no 'modelo_id')
            qs = qs.filter(modelos__id=modelo_id)

        q = (self.q or "").strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
        return qs.order_by("nombre")

    def get_result_label(self, obj: MotorVehiculo):
        nombre = getattr(obj, "nombre", "") or ""
        codigo = getattr(obj, "codigo", "") or ""
        return f"{nombre} — {codigo}" if codigo else nombre


class CajaPorModeloAutocomplete(
    LoginRequiredMixin, _EmpresaMixin, autocomplete.Select2QuerySetView
):
    """Cajas del tenant filtradas por el modelo (forward='modelo')."""

    def get_queryset(self):
        qs = self._qs_empresa(CajaVehiculo.objects.all())

        modelo_id = self.forwarded.get("modelo")
        if modelo_id:
            qs = qs.filter(Q(modelos__id=modelo_id) | Q(modelo_id=modelo_id)).distinct()

        q = (self.q or "").strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
        return qs.order_by("nombre")

    def get_result_label(self, obj: CajaVehiculo):
        nombre = getattr(obj, "nombre", "") or ""
        codigo = getattr(obj, "codigo", "") or ""
        return f"{nombre} — {codigo}" if codigo else nombre


class AnioAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Años disponibles (1970-2026) con opción de agregar años personalizados."""

    def get_queryset(self):
        # Generar años desde 1970 hasta 2026
        current_year = 2026
        start_year = 1970
        years = list(range(current_year, start_year - 1, -1))  # Descendente

        # Convertir a objetos simulados para Select2
        class YearOption:
            def __init__(self, year):
                self.id = year
                self.year = year

        return [YearOption(year) for year in years]

    def get_results(self, context):
        """Retorna los años disponibles."""
        q = (self.q or "").strip()
        years = self.get_queryset()

        if q:
            # Filtrar años que contengan el texto buscado
            try:
                search_year = int(q)
                years = [y for y in years if str(y.year).startswith(str(search_year))]
            except ValueError:
                # Si no es un número, buscar en el texto
                years = [y for y in years if q in str(y.year)]

        return [
            {
                "id": year.id,
                "text": str(year.year),
            }
            for year in years
        ]

    def get_result_label(self, obj):
        return str(obj.year)
