# taller/clientes/dal_views.py
from dal import autocomplete

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from taller.models.clientes import Cliente


class _EmpresaMixin:
    def _qs_empresa(self, qs):
        empresa = getattr(self.request.user, "empresa", None)
        return qs.filter(empresa=empresa) if empresa else qs.none()


class ClientesAutocomplete(LoginRequiredMixin, _EmpresaMixin, autocomplete.Select2QuerySetView):
    """Devuelve clientes del tenant; busca por nombre, rut/ein, email, teléfono."""

    def get_queryset(self):
        qs = self._qs_empresa(Cliente.objects.all())

        q = (self.q or "").strip()
        if q:
            # Construimos un OR dinámico con los campos que existan en tu modelo
            ff = Q()
            if hasattr(Cliente, "nombre"):
                ff |= Q(nombre__icontains=q)
            if hasattr(Cliente, "rut"):
                ff |= Q(rut__icontains=q)
            if hasattr(Cliente, "ein"):
                ff |= Q(ein__icontains=q)
            if hasattr(Cliente, "email"):
                ff |= Q(email__icontains=q)
            if hasattr(Cliente, "telefono"):
                ff |= Q(telefono__icontains=q)
            if ff:
                qs = qs.filter(ff)
        return qs.order_by("nombre")

    # Etiqueta bonita en el dropdown
    def get_result_label(self, obj: Cliente):
        nombre = getattr(obj, "nombre", "") or ""
        rut = getattr(obj, "rut", "") or ""
        ein = getattr(obj, "ein", "") or ""
        id_show = rut or ein
        return f"{nombre} — {id_show}" if id_show else nombre
