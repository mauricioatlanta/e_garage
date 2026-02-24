from django.db import models


class TenantQuerySet(models.QuerySet):
    def for_company(self, empresa):
        """Filtrar por empresa específica"""
        return self.filter(empresa=empresa)


class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def for_request(self, request):
        """Filtrar por empresa del usuario en el request"""
        if not request.user.is_authenticated:
            return self.none()

        empresa = getattr(request.user, "empresa", None)
        if not empresa:
            return self.none()

        return self.get_queryset().for_company(empresa)

    def for_tenant(self, empresa):
        """Filtrar por empresa específica"""
        return self.get_queryset().for_company(empresa)

    def for_company(self, empresa):
        """Alias para for_tenant"""
        return self.for_tenant(empresa)


class TenantScoped(models.Model):
    empresa = models.ForeignKey("taller.Empresa", on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        abstract = True
