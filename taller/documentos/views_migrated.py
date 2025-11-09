"""
Vistas de documentos migradas para usar CountryLangTemplateMixin
Esto reemplaza las vistas FBV que están en views.py con plantillas hardcodeadas
"""

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from taller.forms.documento_form import DocumentoForm
from taller.mixins import CountryLangTemplateMixin
from taller.models import Documento, Tecnico


@method_decorator(login_required, name="dispatch")
class DocumentoListView(CountryLangTemplateMixin, ListView):
    """Vista para listar documentos de la empresa"""

    model = Documento
    context_object_name = "documentos"
    base_template_name = "documentos/lista_documentos.html"
    paginate_by = 20

    def get_template_names(self):
        """Forzar template específico para US/EN"""
        if self.request.path.startswith("/us/"):
            template_name = "taller/us/en/documentos/lista_documentos.html"
            print(f"[DEBUG] DocumentoListView - Using US/EN template: {template_name}")
            return [template_name]
        else:
            template_names = super().get_template_names()
            print(
                f"[DEBUG] DocumentoListView - Using default templates: {template_names}"
            )
            return template_names

    def get_queryset(self):
        """Filtrar documentos por empresa del usuario"""
        try:
            empresa = self.request.user.empresa
            qs = (
                Documento.objects.filter(empresa=empresa)
                .select_related("cliente", "vehiculo", "tecnico_responsable")
                .prefetch_related(
                    "lineas_repuesto__repuesto",
                    "lineas_servicio__servicio",
                    "lineas_otro_servicio",
                )
                .order_by("-fecha_emision", "-id")
            )

            # Los totales ahora se calculan automáticamente en el modelo
            # No necesitamos anotaciones ya que tenemos campos reales

            return qs
        except AttributeError:
            return Documento.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["country"] = getattr(self.request.user.empresa, "pais", "cl").lower()

        # Los totales ya están calculados automáticamente en el modelo
        # No necesitamos calcularlos manualmente aquí

        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name="dispatch")
class DocumentoCreateView(CountryLangTemplateMixin, CreateView):
    """Vista para crear documentos"""

    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/document_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.request.user.empresa

        # Cargar mecánicos activos del taller
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)

        context.update(
            {
                "mecanicos": mecanicos,
                "tecnicos": mecanicos,  # Alias para compatibilidad con templates
                "es_edicion": False,
                "company_country": getattr(self.request, "company_country", None),
                "today": timezone.now().date(),  # Agregar fecha actual
                "template_name": self.get_template_names()[0],
                "pais_emoji": "🇺🇸" if self.request.path.startswith("/us/") else "🇨🇱",
                "empresa": empresa,
                "total": 0,
                "subtotal_repuestos": 0,
                "subtotal_servicios": 0,
                "subtotal_otros_servicios": 0,
                "iva": 0,
                "repuestos": [],
                "debug": True,  # Habilitar debug en template
            }
        )
        return context

    def get_form_kwargs(self):
        """Obtener argumentos para el formulario"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["empresa"] = getattr(self.request.user, "empresa", None)
        kwargs["country"] = "US" if self.request.path.startswith("/us/") else "CL"
        return kwargs

    def get_success_url(self):
        """Redirigir a la lista de documentos después de crear uno exitosamente"""
        if self.request.path.startswith("/us/"):
            return reverse("documentos_us_en:lista_documentos")
        else:
            return reverse("documentos_cl_es:lista_documentos")

    def form_valid(self, form):
        print("[DEBUG DocumentoCreateView] form_valid llamado")
        print(
            f"[DEBUG DocumentoCreateView] Cliente en form.cleaned_data: {form.cleaned_data.get('cliente', 'NO ENCONTRADO')}"
        )
        print(
            f"[DEBUG DocumentoCreateView] Cliente en form.instance: {getattr(form.instance, 'cliente', 'NO ENCONTRADO')}"
        )
        print(
            f"[DEBUG DocumentoCreateView] CSRF token: {self.request.POST.get('csrfmiddlewaretoken', 'NO ENCONTRADO')}"
        )

        form.instance.empresa = self.request.user.empresa

        # Guardar el documento primero
        response = super().form_valid(form)

        # Procesar items dinámicos después de guardar
        self.procesar_items_dinamicos(form)

        # Agregar mensaje de éxito
        from django.contrib import messages

        messages.success(
            self.request,
            f"Documento {form.instance.numero_documento} creado exitosamente para {form.instance.cliente.nombre}.",
        )

        return response

    def form_invalid(self, form):
        print("[DEBUG DocumentoCreateView] form_invalid llamado")
        print(f"[DEBUG DocumentoCreateView] Errores: {form.errors}")
        print(f"[DEBUG DocumentoCreateView] Datos POST: {self.request.POST}")
        return super().form_invalid(form)

    def procesar_items_dinamicos(self, form):
        """Procesa los campos dinámicos de repuestos, servicios y otros servicios"""
        documento = form.instance

        # Procesar repuestos dinámicos
        self.procesar_repuestos_dinamicos(documento)

        # Procesar servicios dinámicos
        self.procesar_servicios_dinamicos(documento)

    def procesar_repuestos_dinamicos(self, documento):
        """Procesa los repuestos agregados dinámicamente"""
        from taller.models.lineas_documento import LineaRepuesto

        # Obtener datos del POST
        codigos = self.request.POST.getlist("rep-0-codigo")
        nombres = self.request.POST.getlist("rep-0-nombre")
        cantidades = self.request.POST.getlist("rep-0-cantidad")
        precios = self.request.POST.getlist("rep-0-precio_unitario")

        print(f"[DEBUG] Procesando repuestos: {len(codigos)} elementos")

        for i, codigo in enumerate(codigos):
            if codigo and nombres[i] and cantidades[i] and precios[i]:
                try:
                    LineaRepuesto.objects.create(
                        documento=documento,
                        codigo=codigo,
                        nombre=nombres[i],
                        cantidad=int(cantidades[i]),
                        precio_unitario=float(precios[i]),
                    )
                    print(f"[DEBUG] Repuesto creado: {codigo} - {nombres[i]}")
                except Exception as e:
                    print(f"[DEBUG] Error creando repuesto: {e}")

    def procesar_servicios_dinamicos(self, documento):
        """Procesa los servicios agregados dinámicamente"""
        from taller.models.lineas_documento import LineaServicio

        # Obtener datos del POST
        nombres = self.request.POST.getlist("serv-0-nombre")
        precios = self.request.POST.getlist("serv-0-precio_unitario")

        print(f"[DEBUG] Procesando servicios: {len(nombres)} elementos")

        for i, nombre in enumerate(nombres):
            if nombre and precios[i]:
                try:
                    LineaServicio.objects.create(
                        documento=documento,
                        nombre=nombre,
                        precio_unitario=float(precios[i]),
                        cantidad=1,
                    )
                    print(f"[DEBUG] Servicio creado: {nombre}")
                except Exception as e:
                    print(f"[DEBUG] Error creando servicio: {e}")

    def render_to_response(self, context, **response_kwargs):
        """Renderizar usando el template correcto"""
        return super().render_to_response(context, **response_kwargs)


@method_decorator(login_required, name="dispatch")
class DocumentoDetailView(CountryLangTemplateMixin, DetailView):
    """Vista para ver detalles de un documento"""

    model = Documento
    context_object_name = "documento"
    base_template_name = "documentos/ver_documento_nuevo.html"

    def get_queryset(self):
        """Asegurar que solo se vean documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.object

        # Obtener líneas del documento
        repuestos = documento.lineas_repuesto.all().select_related("repuesto")
        servicios = documento.lineas_servicio.all().select_related("servicio")
        otros_servicios = documento.lineas_otro_servicio.all()

        # Calcular subtotales
        subtotal_repuestos = sum(
            linea.precio_unitario * linea.cantidad for linea in repuestos
        )
        subtotal_servicios = sum(
            linea.precio_unitario * linea.cantidad for linea in servicios
        )
        subtotal_otros_servicios = sum(
            getattr(otro, "precio_cliente", Decimal("0.00")) for otro in otros_servicios
        )

        # Debug logging
        print(
            f"DEBUG: DocumentoDetailView - Repuestos: {len(repuestos)}, Servicios: {len(servicios)}, Otros: {len(otros_servicios)}"
        )
        print(
            f"DEBUG: subtotal_repuestos: {subtotal_repuestos}, subtotal_servicios: {subtotal_servicios}, subtotal_otros: {subtotal_otros_servicios}"
        )

        subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios

        # Calcular IVA (19% solo sobre repuestos según la lógica de negocio)
        iva = subtotal_repuestos * Decimal("0.19")
        total = subtotal + iva

        print(f"DEBUG: subtotal: {subtotal}, iva: {iva}, total: {total}")

        context.update(
            {
                "lineas_repuesto": repuestos,
                "lineas_servicio": servicios,
                "lineas_otro_servicio": otros_servicios,
                "repuestos": repuestos,  # Mantener compatibilidad
                "servicios": servicios,  # Mantener compatibilidad
                "subtotal_repuestos": subtotal_repuestos,
                "subtotal_servicios": subtotal_servicios,
                "subtotal_otros_servicios": subtotal_otros_servicios,
                "subtotal": subtotal,
                "iva": iva,
                "total": total,
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name="dispatch")
class DocumentoUpdateView(CountryLangTemplateMixin, UpdateView):
    """Vista para editar documentos"""

    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/document_edit.html"

    def get_template_names(self):
        """Sistema robusto de fallback para templates de edición de documentos"""
        from django.template import TemplateDoesNotExist
        from django.template.loader import select_template
        from django.utils.translation import get_language

        # País/idioma desde empresa y request
        empresa = getattr(self.request.user, "empresa", None)
        country = (getattr(empresa, "pais", "CL") or "CL").strip().lower()  # cl/us
        lang = (get_language() or "es").strip().lower()  # es/en

        candidates = [
            f"taller/{country}/{lang}/documentos/document_edit.html",
            f"taller/{country}/{lang}/documentos/editar_documento.html",
            "taller/common/documentos/document_edit.html",  # el que pide la vista
            "taller/common/documentos/editar_documento_nuevo.html",  # template funcional actual
            "taller/documentos/editar_documento_nuevo.html",  # fallback legacy
        ]

        # Devuelve el primero que exista
        try:
            t = select_template(candidates)
            return [t.template.name]
        except TemplateDoesNotExist as e:
            e.args = (", ".join(candidates),)
            raise

    def get_queryset(self):
        """Asegurar que solo se editen documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.object
        empresa = self.request.user.empresa

        # Obtener líneas del documento para edición
        servicios = documento.lineas_servicio.all().select_related("servicio")
        repuestos = documento.lineas_repuesto.all().select_related("repuesto")
        otros_servicios = documento.lineas_otro_servicio.all()

        # Calcular subtotales
        subtotal_repuestos = sum(
            linea.precio_unitario * linea.cantidad for linea in repuestos
        )
        subtotal_servicios = sum(
            linea.precio_unitario * linea.cantidad for linea in servicios
        )
        subtotal_otros_servicios = sum(
            getattr(otro, "precio_cliente", Decimal("0.00")) for otro in otros_servicios
        )

        # Calcular totales
        subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
        iva = subtotal * Decimal("0.19")
        total = subtotal + iva

        # Cargar mecánicos activos del taller
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)

        context.update(
            {
                "documento": documento,
                "servicios": servicios,
                "repuestos": repuestos,
                "otros_servicios": otros_servicios,
                "subtotal_repuestos": subtotal_repuestos,
                "subtotal_servicios": subtotal_servicios,
                "subtotal_otros_servicios": subtotal_otros_servicios,
                "subtotal": subtotal,
                "iva": iva,
                "total": total,
                "mecanicos": mecanicos,
                "tecnicos": mecanicos,  # Alias para compatibilidad con templates
                "es_edicion": True,
            }
        )
        return context

    def get_success_url(self):
        """Redirigir a la vista del documento después de editarlo exitosamente"""
        return reverse("documentos_cl_es:ver_documento", kwargs={"pk": self.object.pk})

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name="dispatch")
class DocumentoDeleteView(CountryLangTemplateMixin, DeleteView):
    """Vista para eliminar documentos"""

    model = Documento
    base_template_name = "documentos/confirmar_eliminar.html"
    success_url = "/documentos/"

    def get_queryset(self):
        """Asegurar que solo se eliminen documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)
