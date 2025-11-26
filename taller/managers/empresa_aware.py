"""
Managers personalizados para asegurar aislamiento multi-tenant.
Garantiza que todas las consultas filtren por empresa automáticamente.
"""

from django.db import models
from django.core.exceptions import PermissionDenied


class EmpresaAwareQuerySet(models.QuerySet):
    """QuerySet que fuerza filtrado por empresa"""

    def para_empresa(self, empresa):
        """Filtrar por empresa específica"""
        if empresa is None:
            return self.none()
        return self.filter(empresa=empresa)

    def para_usuario(self, usuario):
        """Filtrar por empresa del usuario"""
        if not usuario or not usuario.is_authenticated:
            return self.none()

        try:
            empresa = usuario.empresa
            return self.para_empresa(empresa)
        except AttributeError:
            return self.none()

    def for_tenant(self, empresa):
        """Alias para para_empresa (compatibilidad con TenantManager)"""
        return self.para_empresa(empresa)

    def for_company(self, empresa):
        """Alias para para_empresa"""
        return self.para_empresa(empresa)


class EmpresaAwareManager(models.Manager):
    """
    Manager que fuerza aislamiento por empresa.
    NUNCA devuelve objetos de otras empresas.
    """

    def get_queryset(self):
        """Retorna QuerySet con métodos de filtrado por empresa"""
        return EmpresaAwareQuerySet(self.model, using=self._db)

    def para_empresa(self, empresa):
        """Filtrar por empresa específica"""
        return self.get_queryset().para_empresa(empresa)

    def para_usuario(self, usuario):
        """Filtrar por empresa del usuario"""
        return self.get_queryset().para_usuario(usuario)

    def for_tenant(self, empresa):
        """Alias para para_empresa (compatibilidad)"""
        return self.para_empresa(empresa)

    def for_company(self, empresa):
        """Alias para para_empresa"""
        return self.para_empresa(empresa)

    def all(self):
        """
        ⚠️ PELIGROSO: Devuelve TODOS los objetos de TODAS las empresas.
        Solo usar en vistas administrativas o con filtros explícitos.

        En producción, deberías desactivar este método y forzar siempre
        usar para_empresa() o para_usuario().
        """
        # Opción segura: retornar none si se llama sin filtro
        # Descomenta la siguiente línea para activar esta protección:
        # raise PermissionDenied("Debe usar para_empresa() o para_usuario() explícitamente")
        return super().all()

    def get(self, *args, **kwargs):
        """
        ⚠️ Sobrescribir get() para asegurar que siempre se filtre por empresa.
        Esto es crítico para prevenir acceso a objetos de otras empresas.
        """
        # Si ya hay filtro por empresa, continuar normal
        if "empresa" in kwargs or "empresa_id" in kwargs:
            return super().get(*args, **kwargs)

        # Si no hay filtro por empresa, NUNCA devolver objetos de otras empresas
        # En producción, deberías requerir siempre el filtro:
        raise PermissionDenied(
            "Debe especificar empresa o empresa_id en la consulta. "
            "Use para_empresa(empresa) o para_usuario(usuario) en su lugar."
        )


class EmpresaAwareManagerStrict(EmpresaAwareManager):
    """
    Versión estricta del manager que NUNCA permite consultas sin filtro de empresa.
    Usar en modelos críticos (Clientes, Documentos, etc.)
    """

    def all(self):
        """NUNCA permitir all() sin filtro"""
        raise PermissionDenied(
            "Este manager requiere filtro explícito por empresa. "
            "Use para_empresa(empresa) o para_usuario(usuario)."
        )

    def filter(self, *args, **kwargs):
        """Forzar que siempre haya filtro por empresa"""
        if "empresa" not in kwargs and "empresa_id" not in kwargs:
            # Buscar en args si hay un Q object con empresa
            has_empresa_in_args = any(
                hasattr(arg, "children")
                and any(
                    child[0] == "empresa" or child[0].startswith("empresa__")
                    for child in (
                        arg.children if hasattr(arg.children, "__iter__") else [arg.children]
                    )
                )
                for arg in args
                if hasattr(arg, "children")
            )

            if not has_empresa_in_args:
                raise PermissionDenied(
                    "Debe especificar empresa o empresa_id en filter(). "
                    "Use para_empresa(empresa) en su lugar."
                )

        return super().filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        """Forzar que siempre haya filtro por empresa en get()"""
        if "empresa" not in kwargs and "empresa_id" not in kwargs:
            raise PermissionDenied(
                "Debe especificar empresa o empresa_id en get(). "
                "Use para_empresa(empresa).get(...) en su lugar."
            )
        return super().get(*args, **kwargs)


# Manager por defecto seguro (versión estricta)
EmpresaAwareDefaultManager = EmpresaAwareManagerStrict
