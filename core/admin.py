from django.contrib import admin


class TenantAdminMixin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.filter(empresa=request.empresa)
            if hasattr(request, "empresa")
            else qs.none()
        )

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "empresa_id", None) and hasattr(request, "empresa"):
            obj.empresa = request.empresa
        super().save_model(request, obj, form, change)
