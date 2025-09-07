from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import TenantViewMixin
from taller.forms.repuesto import RepuestoForm
from taller.mixins import CountryLangTemplateMixin
from taller.models.repuesto import Repuesto


class RepuestoListView(
    CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, ListView
):
    model = Repuesto
    select_related_fields = ("categoria",)
    paginate_by = 50
    ordering = ("nombre", "id")
    template_name = "repuestos/repuesto_list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(part_number__icontains=q)
                | models.Q(nombre__icontains=q)
                | models.Q(categoria__nombre__icontains=q)
            )
        return qs


class RepuestoDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Repuesto
    select_related_fields = ("categoria",)


class RepuestoCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = "taller/repuesto_form.html"
    success_url = reverse_lazy("taller:repuestos:lista_repuestos")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_template_names(self):
        # Usar template canónico primero
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
        # Usar template canónico primero
        return ["taller/repuesto_form.html", "taller/repuestos/repuesto_form.html"]
