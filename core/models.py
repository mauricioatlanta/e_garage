from django.db import models
from django.utils import timezone

class TenantManager(models.Manager):
    def for_request(self, request):
        empresa = getattr(request, 'empresa', None)
        if empresa:
            return self.filter(empresa=empresa)
        return self.none()

    def for_tenant(self, empresa):
        return self.filter(empresa=empresa)

class TenantScoped(models.Model):
    empresa = models.ForeignKey('taller.Empresa', on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        abstract = True
