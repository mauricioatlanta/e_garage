from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import TenantViewMixin
from taller.forms.repuesto import RepuestoForm
from taller.mixins import CountryLangTemplateMixin
from taller.models.repuesto import Repuesto


def _get_country(request, default="CL"):
    empresa = getattr(request.user, "empresa", None)
    raw = getattr(empresa, "pais", None)

    if not raw:
        raw = getattr(request, "country", None)

    if not raw:
        p = (request.path or "").lower()
        if p.startswith("/us/"):
            raw = "US"
        elif p.startswith("/cl/"):
            raw = "CL"
        elif p.startswith("/mx/"):
            raw = "MX"

    c = str(raw or default).strip().upper()
    if c in ("US", "USA"):
        return "US"
    if c in ("MX", "MEX"):
        return "MX"
    if c in ("BR", "BRA"):
        return "BR"
    return "CL"


def _compat_canonical_redirect(request, view_subpath: str, country: str | None = None):
    if not request.path.startswith("/compat/"):
        return None

    country = country or _get_country(request)
    ns_map = {
        "US": "usa",
        "MX": "mexico",
        "VE": "venezuela",
        "PE": "peru",
        "BR": "brasil",
        "CL": "chile",
    }
    candidates = []
    ns = ns_map.get(country)
    if ns:
        candidates.append(f"{ns}:taller:{view_subpath}")
    candidates.append(f"chile:taller:{view_subpath}")
    candidates.append(f"taller:{view_subpath}")

    for name in candidates:
        try:
            return redirect(reverse(name))
        except NoReverseMatch:
            continue
    return None


class RepuestoListView(CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, ListView):
    model = Repuesto
    select_related_fields = ("categoria",)
    paginate_by = 50
    ordering = ("nombre", "id")
    template_name = "repuestos/repuesto_list.html"

    def dispatch(self, request, *args, **kwargs):
        compat_redirect = _compat_canonical_redirect(request, "repuestos:lista_repuestos")
        if compat_redirect:
            return compat_redirect
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(part_number__icontains=q)
                | models.Q(nombre__icontains=q)
                | models.Q(categoria__nombre__icontains=q)
            )
        self.filtered_queryset = qs
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = getattr(self, "filtered_queryset", None)
        if qs is None:
            qs = self.get_queryset()
        totals = qs.aggregate(total=models.Sum("precio_venta"))
        context["total_value"] = totals.get("total") or Decimal("0")
        context["low_stock_count"] = qs.filter(cantidad_stock__lt=5).count()
        return context


class RepuestoDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Repuesto
    select_related_fields = ("categoria",)


class RepuestoCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = "taller/repuesto_form.html"
    success_url = reverse_lazy("taller:repuestos:lista_repuestos")

    def dispatch(self, request, *args, **kwargs):
        compat_redirect = _compat_canonical_redirect(request, "repuestos:crear_repuesto")
        if compat_redirect:
            return compat_redirect
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_template_names(self):
        return ["taller/repuesto_form.html", "taller/repuestos/repuesto_form.html"]


class RepuestoUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = "taller/repuesto_form.html"
    success_url = reverse_lazy("taller:repuestos:lista_repuestos")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_template_names(self):
        return ["taller/repuesto_form.html", "taller/repuestos/repuesto_form.html"]
