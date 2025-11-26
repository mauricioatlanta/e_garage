import logging
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Cast, Coalesce
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
        # Get the full queryset (before pagination) for calculations
        # Use the filtered queryset if available, otherwise get it from get_queryset
        qs = getattr(self, "filtered_queryset", None)
        if qs is None:
            # Get queryset base (already filtered by empresa via TenantViewMixin)
            qs = super().get_queryset()
            # Apply search filter if present
            q = (self.request.GET.get("q") or "").strip()
            if q:
                qs = qs.filter(
                    models.Q(part_number__icontains=q)
                    | models.Q(nombre__icontains=q)
                    | models.Q(categoria__nombre__icontains=q)
                )

        # DEBUG: Log all repuestos in queryset
        logger = logging.getLogger(__name__)
        repuestos_list = list(qs.values("id", "nombre", "precio_venta", "cantidad_stock"))
        logger.info(f"[REPUESTOS DEBUG] Total repuestos en queryset: {len(repuestos_list)}")

        # Calculate manual total for comparison
        manual_total = Decimal("0")
        for rep in repuestos_list:
            precio = Decimal(str(rep.get("precio_venta") or 0))
            cantidad = Decimal(str(rep.get("cantidad_stock") or 0))
            subtotal = precio * cantidad
            manual_total += subtotal
            logger.info(
                f"[REPUESTOS DEBUG] {rep.get('nombre')}: precio=${precio}, cantidad={cantidad}, subtotal=${subtotal}"
            )

        logger.info(f"[REPUESTOS DEBUG] Total manual calculado: ${manual_total}")

        # Calculate total value: precio_venta * cantidad_stock for each repuesto
        # Cast cantidad_stock to DecimalField for proper multiplication
        # Handle NULL values by treating them as 0
        precio = Coalesce(
            F("precio_venta"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
        cantidad = Cast(
            Coalesce(F("cantidad_stock"), Value(0)),
            output_field=DecimalField(max_digits=10, decimal_places=0),
        )
        total_expr = ExpressionWrapper(
            precio * cantidad, output_field=DecimalField(max_digits=14, decimal_places=2)
        )
        totals = qs.aggregate(
            total=Coalesce(
                Sum(total_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        sql_total = totals.get("total") or Decimal("0")
        logger.info(f"[REPUESTOS DEBUG] Total SQL agregado: ${sql_total}")
        logger.info(f"[REPUESTOS DEBUG] Diferencia: ${manual_total - sql_total}")

        context["total_value"] = sql_total
        context["low_stock_count"] = qs.filter(cantidad_stock__lt=5).count()
        return context


class RepuestoDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Repuesto
    select_related_fields = ("categoria",)


class RepuestoCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = "taller/common/repuestos/repuesto_form.html"
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
        return ["taller/common/repuestos/repuesto_form.html", "taller/repuestos/repuesto_form.html"]


class RepuestoUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = "taller/common/repuestos/repuesto_form.html"
    success_url = reverse_lazy("taller:repuestos:lista_repuestos")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_template_names(self):
        return ["taller/common/repuestos/repuesto_form.html", "taller/repuestos/repuesto_form.html"]
