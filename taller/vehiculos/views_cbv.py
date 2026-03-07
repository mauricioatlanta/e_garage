import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
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

    def get_initial(self):
        initial = super().get_initial()
        prefill = (self.request.GET.get("prefill_cliente") or "").strip()
        if prefill.isdigit():
            initial["cliente"] = int(prefill)
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        prefill = (self.request.GET.get("prefill_cliente") or "").strip()
        if prefill.isdigit():
            form.fields["cliente"].initial = int(prefill)
            form.instance.cliente_id = int(prefill)

        # Detectar país y agregar campos USA si es necesario
        empresa = getattr(self.request, "empresa", getattr(self.request.user, "empresa", None))
        country = getattr(empresa, "pais", "CL") if empresa else "CL"

        if str(country).strip().upper() == "US":
            form.add_usa_fields()

        return form

    def _get_next_url(self):
        """Obtiene la URL de redirección desde POST, GET o sesión (igual que ClienteCreateView)."""
        from urllib.parse import unquote

        raw_next = (self.request.POST.get("next") or self.request.GET.get("next") or "").strip()
        if not raw_next:
            return None
        next_url = unquote(raw_next).strip()
        if next_url and not next_url.startswith(("http://", "https://", "/")):
            next_url = "/" + next_url
        url_to_check = (
            self.request.build_absolute_uri(next_url) if next_url.startswith("/") else next_url
        )
        if url_has_allowed_host_and_scheme(
            url=url_to_check,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url if next_url.startswith("/") else url_to_check
        return None

    def get_success_url(self):
        next_url = self._get_next_url()
        if next_url:
            return next_url
        empresa = getattr(self.request.user, "empresa", None)
        if empresa and getattr(empresa, "pais", None) == "US":
            return reverse("usa:taller:vehiculos:lista_vehiculos")
        return reverse("chile:taller:vehiculos:lista_vehiculos")

    def form_valid(self, form):
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        from django.shortcuts import redirect

        # Asignar empresa automáticamente (TenantScoped)
        empresa_req = getattr(self.request, "empresa", None)
        if empresa_req:
            form.instance.empresa = empresa_req

        self.object = form.save()
        next_url = self.get_success_url()

        # Si volvemos al documento, agregar new_vehiculo_id y prefill_cliente
        if next_url and "documentos" in next_url:
            parsed = urlparse(next_url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            params["new_vehiculo_id"] = [str(self.object.pk)]
            if self.object.cliente_id:
                c = getattr(self.object, "cliente", None)
                params["prefill_cliente"] = [str(self.object.cliente_id)]
                if c:
                    nombre = getattr(c, "nombre_completo", None) or ""
                    if not nombre:
                        nombre = f"{(getattr(c, 'nombre', '') or '').strip()} {(getattr(c, 'apellido', '') or '').strip()}".strip()
                    params["prefill_cliente_nombre"] = [nombre or str(c)]
                    params["prefill_cliente_email"] = [getattr(c, "email", "") or ""]
                    params["prefill_cliente_telefono"] = [getattr(c, "telefono", "") or ""]
                else:
                    params["prefill_cliente_nombre"] = [str(self.object.cliente_id)]
            new_query = urlencode(params, doseq=True)
            next_url = urlunparse(parsed._replace(query=new_query))
            return redirect(next_url)

        return redirect(next_url)

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
        ctx["next"] = self.request.GET.get("next", "").strip() or None
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
