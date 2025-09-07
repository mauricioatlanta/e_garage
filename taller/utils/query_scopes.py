from django.db import models


def scoped_qs(qs: models.QuerySet, request) -> models.QuerySet:
    """Aplica scopes de seguridad basados en el usuario y empresa actual

    Args:
        qs (QuerySet): QuerySet original a filtrar
        request (HttpRequest): Objeto request con usuario autenticado

    Returns:
        QuerySet: QuerySet filtrado según los permisos
    """
    if hasattr(qs.model, "empresa") and hasattr(request.user, "empresa"):
        return qs.filter(empresa=request.user.empresa)
    return qs


class QueryScope:
    """Clase base para aplicar scopes de consulta por empresa y país"""

    @classmethod
    def by_empresa(cls, empresa):
        """Filtra queryset por empresa"""
        return cls.get_queryset().filter(empresa=empresa)

    @classmethod
    def by_user_empresa(cls, user):
        """Filtra por empresa del usuario actual"""
        return cls.by_empresa(user.empresa)

    @classmethod
    def by_pais(cls, pais):
        """Filtra queryset por país"""
        return cls.get_queryset().filter(pais=pais)

    @classmethod
    def by_user_pais(cls, user):
        """Filtra por país de la empresa del usuario"""
        return cls.by_pais(user.empresa.pais)


class ScopeManager(models.Manager):
    """Manager personalizado que incluye los scopes por defecto"""

    def get_queryset(self):
        return super().get_queryset()

    def by_empresa(self, empresa):
        return self.get_queryset().filter(empresa=empresa)

    def by_user_empresa(self, user):
        return self.by_empresa(user.empresa)

    def by_pais(self, pais):
        return self.get_queryset().filter(pais=pais)

    def by_user_pais(self, user):
        return self.by_pais(user.empresa.pais)

    def by_empresa(self, empresa):
        return self.get_queryset().filter(empresa=empresa)

    def by_user_empresa(self, user):
        return self.by_empresa(user.empresa)

    def by_pais(self, pais):
        return self.get_queryset().filter(pais=pais)

    def by_user_pais(self, user):
        return self.by_pais(user.empresa.pais)
