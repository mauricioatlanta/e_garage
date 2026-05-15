"""
Mixins para vistas que garantizan aislamiento multi-tenant.
Verifican automáticamente que los objetos pertenezcan a la empresa del usuario.
"""

from django.core.exceptions import PermissionDenied, Http404
from django.db.models import Model


class EmpresaRequiredMixin:
    """
    Mixin que garantiza que todas las operaciones se limiten a la empresa del usuario.

    Uso:
        class ClienteDetailView(EmpresaRequiredMixin, DetailView):
            model = Cliente

    Este mixin:
    1. Filtra automáticamente el queryset por empresa
    2. Verifica que el objeto obtenido pertenezca a la empresa del usuario
    3. Asigna automáticamente la empresa al crear objetos
    """

    def get_queryset(self):
        """Filtrar queryset por empresa del usuario"""
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            return queryset.model.objects.none()

        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return queryset.model.objects.none()

        # Si el queryset tiene método para_empresa, usarlo
        if hasattr(queryset, "para_empresa"):
            return queryset.para_empresa(empresa)

        # Si el modelo tiene campo empresa, filtrar manualmente
        if hasattr(queryset.model, "empresa"):
            return queryset.filter(empresa=empresa)

        # Si el modelo tiene método for_tenant (compatibilidad)
        if hasattr(queryset, "for_tenant"):
            return queryset.for_tenant(empresa)

        return queryset.model.objects.none()

    def get_object(self, queryset=None):
        """
        Obtener objeto y verificar que pertenezca a la empresa del usuario.
        Lanza 404 si no pertenece (ocultar existencia de objetos de otras empresas).
        """
        obj = super().get_object(queryset)

        if not self.request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")

        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            raise PermissionDenied("Usuario sin empresa asignada")

        # Verificar que el objeto pertenezca a la empresa
        obj_empresa = getattr(obj, "empresa", None)
        if obj_empresa != empresa:
            # Lanzar 404 en lugar de 403 para ocultar existencia de objetos de otras empresas
            raise Http404("Objeto no encontrado")

        return obj

    def form_valid(self, form):
        """
        Al guardar formularios, asignar automáticamente la empresa del usuario.
        """
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            raise PermissionDenied("Usuario sin empresa asignada")

        # Si el objeto tiene campo empresa y no está asignado, asignarlo
        if hasattr(form.instance, "empresa") and not form.instance.empresa_id:
            form.instance.empresa = empresa

        return super().form_valid(form)


class EmpresaFilterMixin:
    """
    Mixin más ligero que solo filtra el queryset por empresa.
    No verifica pertenencia (útil para listas donde queryset ya está filtrado).
    """

    def get_queryset(self):
        """Filtrar queryset por empresa del usuario"""
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            return queryset.model.objects.none()

        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return queryset.model.objects.none()

        # Si el queryset tiene método para_empresa, usarlo
        if hasattr(queryset, "para_empresa"):
            return queryset.para_empresa(empresa)

        # Si el modelo tiene campo empresa, filtrar manualmente
        if hasattr(queryset.model, "empresa"):
            return queryset.filter(empresa=empresa)

        return queryset


class EmpresaContextMixin:
    """
    Mixin que agrega la empresa al contexto de la plantilla.
    Útil para mostrar información de la empresa en todas las vistas.
    """

    def get_context_data(self, **kwargs):
        """Agregar empresa al contexto"""
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            try:
                context["empresa"] = self.request.user.empresa
                context["empresa_nombre"] = self.request.user.empresa.nombre_taller
                context["empresa_pais"] = getattr(self.request.user.empresa, "pais", "CL")
            except AttributeError:
                context["empresa"] = None

        # También agregar desde request (si middleware lo inyectó)
        context["empresa"] = context.get("empresa") or getattr(self.request, "empresa", None)

        return context


class EmpresaOwnershipMixin:
    """
    Mixin que verifica explícitamente la pertenencia de un objeto a la empresa.
    Útil para operaciones críticas donde necesitas verificación adicional.
    """

    def verificar_pertenencia(self, obj: Model, empresa=None):
        """
        Verificar que un objeto pertenezca a la empresa especificada.
        Lanza PermissionDenied si no pertenece.
        """
        if empresa is None:
            empresa = getattr(self.request.user, "empresa", None)

        if not empresa:
            raise PermissionDenied("Usuario sin empresa asignada")

        obj_empresa = getattr(obj, "empresa", None)
        if obj_empresa != empresa:
            raise PermissionDenied(
                f"El objeto no pertenece a la empresa del usuario. "
                f"Esperada: {empresa.id}, Obtenida: {obj_empresa.id if obj_empresa else None}"
            )

        return True


class EmpresaScopedMixin(EmpresaRequiredMixin, EmpresaContextMixin):
    """
    Mixin combinado que incluye:
    - Filtrado automático por empresa
    - Verificación de pertenencia
    - Contexto de empresa
    Útil para la mayoría de vistas CRUD.
    """

    pass
