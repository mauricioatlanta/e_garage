import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import TenantViewMixin
from taller.mixins import CountryLangTemplateMixin
from taller.models.clientes import Cliente
from taller.models.extras_vehiculo import ColorVehiculo
from taller.models.marca import Marca
from taller.models.vehiculos import Vehiculo

from .forms import VehiculoForm

try:
    from taller.models.catalogo import CatalogoModeloAuto  # Nuestro nuevo catálogo
    from taller.models.marcas_usa import MarcaVehiculo as MarcaVehiculoUSA
    from taller.models.marcas_usa import ModeloVehiculo as ModeloVehiculoUSA
except Exception:  # pragma: no cover - si no existen modelos USA
    MarcaVehiculoUSA = ModeloVehiculoUSA = CatalogoModeloAuto = None


class VehiculoListView(CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, ListView):
    model = Vehiculo
    base_template_name = "vehiculos/vehiculo_list.html"  # Usar template autoritativo
    select_related_fields = ("cliente",)
    ordering = ("-id",)
    paginate_by = 50
    # Nombre explícito para que la plantilla 'vehiculos.html' que itera sobre 'vehiculos' funcione
    context_object_name = "vehiculos"

    def get_template_names(self):
        """Override template selection for USA users to use simple template"""
        if self.request.path.startswith("/us/"):
            return ["taller/us/en/vehiculos/vehiculo_list_simple.html"]
        return super().get_template_names()

    def get_queryset(self):
        # Fallback: en tests puede que middleware no inyecte request.empresa; usar empresa de user
        if not getattr(self.request, "empresa", None) and getattr(
            self.request.user, "empresa", None
        ):
            qs = self.model.objects.for_tenant(self.request.user.empresa)
        else:
            qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(patente__icontains=q)
                | models.Q(vin__icontains=q)
                | models.Q(modelo__nombre__icontains=q)
                | models.Q(marca__nombre__icontains=q)
            )
        return qs


class VehiculoDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Vehiculo
    template_name = "taller/vehiculos/vehiculo_detail.html"
    select_related_fields = ("cliente",)


log = logging.getLogger(__name__)


class VehiculoCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = "taller/vehiculos/crear_vehiculo.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pasar el usuario y request para que el formulario adapte campos (Chile vs USA)
        kwargs["user"] = self.request.user
        kwargs["request"] = self.request
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Detectar país y agregar campos USA si es necesario
        empresa = getattr(self.request, "empresa", getattr(self.request.user, "empresa", None))
        country = getattr(empresa, "pais", "CL") if empresa else "CL"

        if str(country).strip().upper() == "US":
            form.add_usa_fields()

        return form

    def form_valid(self, form):
        # Asignar empresa automáticamente (TenantScoped)
        # Asignar empresa usando getattr para evitar warnings de tipo estático
        empresa_req = getattr(self.request, "empresa", None)
        if empresa_req:
            form.instance.empresa = empresa_req
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        empresa = getattr(self.request, "empresa", getattr(self.request.user, "empresa", None))
        raw_country = getattr(empresa, "pais", None) or "CL"
        country = str(raw_country).strip().upper()

        # Flag de diagnóstico para forzar USA (solo staff & DEBUG)
        if self.request.GET.get("force_us") == "1" and self.request.user.is_staff:
            # Rama diagnóstica para forzar USA en entorno debug
            log.warning(
                "[FORCE_US] Forzando country=US para usuario=%s (valor real=%s)",
                self.request.user.username,
                country,
            )
            country = "US"

        if country not in ("CL", "US", "MX"):
            log.warning(
                "[VehiculoCreateView] country desconocido '%s' normalizado a 'CL' (usuario=%s, empresa=%s)",
                country,
                self.request.user.username,
                getattr(empresa, "id", None),
            )
            country = "CL"

        ctx["country"] = country
        ctx["SHOW_DEBUG"] = True  # Para mostrar [DEBUG country: ...] en el template
        ctx["debug_empresa_pais"] = (
            f"empresa={getattr(empresa,'id',None)} pais={country} usuario={self.request.user.username}"
        )

        # Listas auxiliares (fallback cuando no se usa DAL o para selects básicos)
        ctx["clientes"] = Cliente.objects.filter(empresa=empresa)[
            :500
        ]  # BLINDAJE: Filtrado por empresa
        ctx["colores"] = ColorVehiculo.get_colores_para_pais(country)  # CORREGIDO: Colores por país
        if country == "US":
            # Usar nuestro catálogo importado para USA
            if CatalogoModeloAuto:
                ctx["marcas_usa"] = CatalogoModeloAuto.get_marcas_activas()[:500]
                ctx["usa_catalogo_disponible"] = True
            elif MarcaVehiculoUSA:
                ctx["marcas_usa"] = (
                    MarcaVehiculoUSA.objects.filter(activa=True)
                    .only("id", "nombre")
                    .order_by("nombre")
                )
            if ModeloVehiculoUSA:
                ctx["modelos_usa"] = (
                    ModeloVehiculoUSA.objects.filter(activo=True)
                    .only("id", "nombre")
                    .order_by("nombre")
                )
        else:
            ctx["marcas"] = (
                Marca.objects.filter(country=country).only("id", "nombre").order_by("nombre")
            )
        return ctx


class VehiculoUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = "taller/vehiculos/vehiculo_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        # Los valores especiales __nuevo__ ahora se manejan en el método save() del formulario
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        empresa = getattr(self.request, "empresa", getattr(self.request.user, "empresa", None))
        country = getattr(empresa, "pais", "CL") if empresa else "CL"
        ctx["country"] = country
        ctx["clientes"] = (
            Cliente.objects.filter(empresa=empresa)[:500] if empresa else Cliente.objects.none()
        )  # BLINDAJE: Filtrado por empresa
        ctx["colores"] = ColorVehiculo.get_colores_para_pais(country)  # CORREGIDO: Colores por país
        if country == "US" and MarcaVehiculoUSA:
            ctx["marcas_usa"] = MarcaVehiculoUSA.objects.filter(activa=True).order_by("nombre")
            ctx["modelos_usa"] = (
                ModeloVehiculoUSA.objects.filter(activo=True).order_by("nombre")
                if ModeloVehiculoUSA
                else []
            )
        else:
            ctx["marcas"] = Marca.objects.filter(country=country).order_by("nombre")
        ctx["modo"] = "editar"
        return ctx
