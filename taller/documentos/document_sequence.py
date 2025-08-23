from django.db import models
from django.db.models import Index
from core.models import TenantScoped

class DocumentSequence(TenantScoped):
    tipo = models.CharField(max_length=4)
    next_number = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("empresa", "tipo")]
        indexes = [Index(fields=["empresa", "tipo"])]
