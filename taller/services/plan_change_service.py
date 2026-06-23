from taller.models.team_member import TeamMember


class PlanLimitValidation:
    # Soporta tanto los códigos de negocio (express/taller/pro) como
    # los códigos internos canónicos (entry/growth/business).
    LIMITES_PLANES = {
        # Nombres de negocio (usados en UI y nuevos flows)
        'express': 1,
        'taller': 4,
        'pro': 10,
        # Códigos internos canónicos (plan_catalog.py)
        'entry': 1,
        'growth': 4,
        'business': 10,
        # Fallbacks
        'trial': 1,
        'basic': 1,
        'premium': 4,
        'enterprise': 10,
    }

    @classmethod
    def get_count(cls, empresa) -> int:
        """Cuenta usuarios activos (owner incluido, ya es TeamMember con rol=Owner)."""
        return TeamMember.objects.filter(empresa=empresa, is_active=True).count()

    @classmethod
    def can_add_user(cls, empresa) -> tuple[bool, int, int]:
        """Verifica si la empresa puede agregar un usuario más según su plan.
        Retorna (puede_agregar, usuarios_actuales, limite_maximo).
        """
        plan_codigo = getattr(empresa, 'plan', 'express') or 'express'
        limite = cls.LIMITES_PLANES.get(str(plan_codigo).lower(), 1)
        count = cls.get_count(empresa)
        return count < limite, count, limite

    @classmethod
    def validar_cupo_usuario(cls, empresa_actual) -> tuple[bool, int, int]:
        """Alias legacy — usar can_add_user en código nuevo."""
        return cls.can_add_user(empresa_actual)
