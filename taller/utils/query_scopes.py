from django.db import models

from taller.utils.empresa import get_user_empresa_safe


def scoped_qs(qs: models.QuerySet, request) -> models.QuerySet:
    """Filtra el queryset por la empresa del request, resolviendo owner y TeamMember.

    Si request.empresa es None (usuario sin empresa), devuelve el queryset sin
    filtrar — el caller es responsable de no invocar esto sin usuario autenticado.
    """
    empresa = getattr(request, "empresa", None)
    if hasattr(qs.model, "empresa") and empresa is not None:
        return qs.filter(empresa=empresa)
    return qs


class QueryScope:
    """Clase base para aplicar scopes de consulta por empresa y país."""

    @classmethod
    def by_empresa(cls, empresa):
        return cls.get_queryset().filter(empresa=empresa)

    @classmethod
    def by_user_empresa(cls, user):
        empresa = get_user_empresa_safe(user)
        if empresa is None:
            return cls.get_queryset().none()
        return cls.by_empresa(empresa)

    @classmethod
    def by_pais(cls, pais):
        return cls.get_queryset().filter(pais=pais)

    @classmethod
    def by_user_pais(cls, user):
        empresa = get_user_empresa_safe(user)
        if empresa is None:
            return cls.get_queryset().none()
        return cls.by_pais(empresa.pais)


class ScopeManager(models.Manager):
    """Manager personalizado que incluye los scopes por defecto."""

    def get_queryset(self):
        return super().get_queryset()

    def by_empresa(self, empresa):
        return self.get_queryset().filter(empresa=empresa)

    def by_user_empresa(self, user):
        empresa = get_user_empresa_safe(user)
        if empresa is None:
            return self.none()
        return self.by_empresa(empresa)

    def by_pais(self, pais):
        return self.get_queryset().filter(pais=pais)

    def by_user_pais(self, user):
        empresa = get_user_empresa_safe(user)
        if empresa is None:
            return self.none()
        return self.by_pais(empresa.pais)
