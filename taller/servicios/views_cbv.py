from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import get_language
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.views import TenantViewMixin
from taller.common.mixins.context_return import ContextReturnCreateMixin
from taller.servicios.models import CategoriaServicio, Servicio, SubcategoriaServicio
from taller.templatetags.country_url import reverse_country_url


class ServicioListView(LoginRequiredMixin, TenantViewMixin, ListView):
    model = Servicio
    template_name = "taller/common/servicios/servicios_menu.html"
    select_related_fields = ("categoria", "subcategoria")
    paginate_by = 50
    ordering = ("nombre", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(nombre__icontains=q)
                | models.Q(categoria__nombre__icontains=q)
                | models.Q(subcategoria__nombre__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = CategoriaServicio.objects.all()
        context["subcategorias"] = SubcategoriaServicio.objects.all()
        return context


class ServicioDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Servicio
    template_name = "taller/common/servicios/servicio_detail.html"
    select_related_fields = ("categoria", "subcategoria")

    def get_template_names(self):
        return ["taller/common/servicios/servicio_detail.html", "servicios/servicio_detail.html"]


class ServicioCreateView(ContextReturnCreateMixin, LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Servicio
    template_name = "taller/common/servicios/crear_servicio.html"
    fields = ["nombre", "categoria", "precio_base"]

    def get_template_names(self):
        return ["taller/common/servicios/crear_servicio.html", "servicios/crear_servicio.html"]

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("prefill_nombre"):
            initial["nombre"] = self.request.GET.get("prefill_nombre")
        return initial

    def form_valid(self, form):
        empresa = getattr(self.request, "empresa", None) or getattr(
            self.request.user, "empresa", None
        )
        if empresa and not getattr(form.instance, "empresa_id", None):
            form.instance.empresa = empresa

        if not form.cleaned_data.get("categoria") and form.cleaned_data.get("subcategoria"):
            form.instance.categoria = form.cleaned_data["subcategoria"].categoria

        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        try:
            from taller.servicios.views import _detectar_pais
            country_code = _detectar_pais(self.request)
        except Exception:
            country_code = 'CL'
        if 'categoria' in form.fields:
            from taller.servicios.models import CategoriaServicio
            EXCLUDE_CODES = ['ELECTRICO','FRENOS','MANT','electrico','frenos','motor',
                             'suspension','transmision','emergencias','especiales']
            qs = CategoriaServicio.objects.filter(
                country=country_code
            ).exclude(code__in=EXCLUDE_CODES).order_by('orden', 'code')
            form.fields['categoria'].queryset = qs
            form.fields['categoria'].label_from_instance = lambda obj: obj.get_label()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from taller.servicios.views import _detectar_pais
            from django.utils.translation import get_language
            from taller.servicios.views import COUNTRY_LANGUAGE_MAP
            country_code = _detectar_pais(self.request)
            request_lang = get_language() or 'es'
            context['language'] = COUNTRY_LANGUAGE_MAP.get(country_code, request_lang[:2])
        except Exception:
            context['language'] = 'es'
        context['return_to'] = self.request.GET.get('return_to', '')
        return context

    def get_default_success_url(self):
        return reverse_country_url(self.request, "servicios:servicios_menu")

    def get_created_object_payload(self):
        servicio = getattr(self, "object", None)
        if not servicio:
            return {}

        payload = {
            "created_servicio_id": servicio.pk,
            "created_servicio_label": servicio.nombre or f"Servicio #{servicio.pk}",
            "created_servicio_precio": str(getattr(servicio, "precio_base", 0) or 0),
        }

        target_row = (
            self.request.POST.get("target_row") or self.request.GET.get("target_row") or ""
        ).strip()
        if target_row:
            payload["target_row"] = target_row

        return payload

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = CategoriaServicio.objects.all()
        context["subcategorias"] = SubcategoriaServicio.objects.all()
        context["language"] = get_language() or "es"
        context["return_to"] = self.get_return_to() or ""
        return context


class ServicioUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Servicio
    template_name = "taller/common/servicios/editar_servicio.html"
    fields = ["nombre", "categoria", "subcategoria"]

    def get_template_names(self):
        return ["taller/common/servicios/editar_servicio.html", "servicios/editar_servicio.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = CategoriaServicio.objects.all()
        context["subcategorias"] = SubcategoriaServicio.objects.all()
        return context


class ServicioDeleteView(LoginRequiredMixin, TenantViewMixin, DeleteView):
    model = Servicio
    template_name = "taller/common/servicios/eliminar_servicio_confirmar.html"

    def get_template_names(self):
        return [
            "taller/common/servicios/eliminar_servicio_confirmar.html",
            "servicios/eliminar_servicio_confirmar.html",
        ]

    def get_success_url(self):
        from taller.templatetags.country_url import reverse_country_url

        return reverse_country_url(self.request, "servicios:servicios_menu")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = CategoriaServicio.objects.all()
        context["subcategorias"] = SubcategoriaServicio.objects.all()
        return context
