from django.db import models


class RepuestoDocumento(models.Model):
    # ... tus campos ...
    class Meta:
        indexes = [
            models.Index(fields=["documento"]),
            models.Index(fields=["mecanico"]),
            models.Index(fields=["documento", "mecanico"]),
        ]
