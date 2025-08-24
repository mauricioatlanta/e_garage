from django.views.generic import ListView, DetailView, CreateView, UpdateView

class TenantViewMixin:
    select_related_fields: tuple[str, ...] = ()
    prefetch_related_fields: tuple[str, ...] = ()
    paginate_by = 50  # ajusta por vista si necesitas

    def get_queryset(self):
        # Verificar si el manager tiene el método for_request
        if hasattr(self.model.objects, 'for_request'):
            qs = self.model.objects.for_request(self.request)
        else:
            # Fallback: usar queryset base y filtrar por empresa si existe
            qs = self.model.objects.all()
            if hasattr(self.model, 'empresa') and hasattr(self.request, 'empresa'):
                qs = qs.filter(empresa=self.request.empresa)
        
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
        if not getattr(form.instance, "empresa_id", None):
            form.instance.empresa = self.request.empresa
        return super().form_valid(form)
