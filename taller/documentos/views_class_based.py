from django.http import Http404

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import CreateView, UpdateView

from taller.documentos.forms import DocumentoForm
from taller.mixins import CountryLangTemplateMixin
from taller.models import Documento, Empresa


class DocumentoFormView(CountryLangTemplateMixin, LoginRequiredMixin, CreateView):
    """Vista unificada para crear documentos usando mixin de país/idioma"""

    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/documento_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        # Get country from empresa
        try:
            empresa = self.request.user.empresa
            country = getattr(empresa, "pais", "CL") if empresa else "CL"
        except AttributeError:
            country = "CL"

        kwargs["country"] = country
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener empresa del usuario
        try:
            empresa = self.request.user.empresa
        except AttributeError:
            empresa, created = Empresa.objects.get_or_create(
                user=self.request.user,
                defaults={"nombre_taller": f"Taller de {self.request.user.username}"},
            )

        # Obtener country code
        company_country = getattr(empresa, "pais", "CL") if empresa else "CL"

        # URLs para navegación - Generar URL con prefijo de país correcto
        from django.urls import NoReverseMatch

        try:
            # Detectar país desde el path del request
            if self.request.path.startswith("/us/"):
                # Para USA, usar namespace usa:company_settings
                settings_url = reverse("usa:company_settings")
            elif self.request.path.startswith("/cl/"):
                # Para Chile, intentar chile:company_settings primero, luego fallback
                try:
                    settings_url = reverse("company_settings")
                except NoReverseMatch:
                    settings_url = reverse("company_settings")
            else:
                # Fallback: usar default
                settings_url = reverse("company_settings")
        except NoReverseMatch:
            # Fallback: construir URL manualmente basada en el path
            if self.request.path.startswith("/us/"):
                settings_url = "/us/settings/"
            else:
                settings_url = reverse("company_settings")
        except Exception:
            # Fallback de emergencia
            if self.request.path.startswith("/us/"):
                settings_url = "/us/settings/"
            else:
                settings_url = reverse("company_settings")

        context.update(
            {
                "documento": None,
                "es_edicion": False,
                "company_country": company_country,
                "today": now().date(),
                "settings_url": settings_url,
            }
        )

        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


class DocumentoUpdateView(CountryLangTemplateMixin, LoginRequiredMixin, UpdateView):
    """Vista unificada para editar documentos usando mixin de país/idioma"""

    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/documento_form.html"

    def get_object(self, queryset=None):
        """Asegurar que solo se puedan editar documentos de la empresa del usuario"""
        try:
            empresa = self.request.user.empresa
        except AttributeError:
            raise Http404("Usuario sin empresa asociada")

        pk = self.kwargs.get("pk")
        try:
            return get_object_or_404(Documento, pk=pk, empresa=empresa)
        except Http404:
            # 🔒 SEGURIDAD: Filtrar por empresa incluso en debug para aislamiento multi-tenant
            # Debug info en caso de error
            documento_exists = Documento.objects.filter(pk=pk, empresa=empresa).first()
            if documento_exists:
                messages.error(self.request, f"Documento {pk} no pertenece a tu empresa")
            else:
                messages.error(self.request, f"Documento {pk} no encontrado")
            raise

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        # Get country from empresa
        try:
            empresa = self.request.user.empresa
            country = getattr(empresa, "pais", "CL") if empresa else "CL"
        except AttributeError:
            country = "CL"

        kwargs["country"] = country
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener empresa del usuario
        try:
            empresa = self.request.user.empresa
        except AttributeError:
            empresa = None

        # Obtener country code
        company_country = getattr(empresa, "pais", "CL") if empresa else "CL"

        # URLs para navegación - Generar URL con prefijo de país correcto
        from django.urls import NoReverseMatch

        try:
            # Detectar país desde el path del request
            if self.request.path.startswith("/us/"):
                # Para USA, usar namespace usa:company_settings
                settings_url = reverse("usa:company_settings")
            elif self.request.path.startswith("/cl/"):
                # Para Chile, intentar chile:company_settings primero, luego fallback
                try:
                    settings_url = reverse("company_settings")
                except NoReverseMatch:
                    settings_url = reverse("company_settings")
            else:
                # Fallback: usar default
                settings_url = reverse("company_settings")
        except NoReverseMatch:
            # Fallback: construir URL manualmente basada en el path
            if self.request.path.startswith("/us/"):
                settings_url = "/us/settings/"
            else:
                settings_url = reverse("company_settings")
        except Exception:
            # Fallback de emergencia
            if self.request.path.startswith("/us/"):
                settings_url = "/us/settings/"
            else:
                settings_url = reverse("company_settings")

        context.update(
            {
                "documento": self.object,
                "es_edicion": True,
                "company_country": company_country,
                "today": now().date(),
                "settings_url": settings_url,
            }
        )

        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)
