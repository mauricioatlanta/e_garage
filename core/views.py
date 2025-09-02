from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.core.exceptions import PermissionDenied

class TenantViewMixin:
    select_related_fields: tuple[str, ...] = ()
    prefetch_related_fields: tuple[str, ...] = ()
    paginate_by = 50  # ajusta por vista si necesitas

    def get_queryset(self):
        # BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa del usuario
        if not self.request.user.is_authenticated:
            return self.model.objects.none()
        
        empresa = getattr(self.request.user, 'empresa', None)
        if not empresa:
            return self.model.objects.none()
        
        # Verificar si el manager tiene el método for_tenant
        if hasattr(self.model.objects, 'for_tenant'):
            qs = self.model.objects.for_tenant(empresa)
        else:
            # Fallback: usar queryset base y filtrar por empresa
            if hasattr(self.model, 'empresa'):
                qs = self.model.objects.filter(empresa=empresa)
            else:
                qs = self.model.objects.all()
        
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        if self.prefetch_related_fields:
            qs = qs.prefetch_related(*self.prefetch_related_fields)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar country al contexto
        context['country'] = getattr(self.request, 'country', 'cl')
        context['company_country'] = getattr(self.request, 'company_country', None)  # viene del middleware
        return context

    def form_valid(self, form):
        # BLINDAJE MULTI-TENANT: SIEMPRE asignar empresa del usuario
        empresa = getattr(self.request.user, 'empresa', None)
        if not empresa:
            raise PermissionDenied("Usuario sin empresa asignada")
        
        if not getattr(form.instance, "empresa_id", None):
            form.instance.empresa = empresa
        return super().form_valid(form)
