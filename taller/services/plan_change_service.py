from django.contrib.auth import get_user_model
from django.db.models import Q

class PlanLimitValidation:
    LIMITES_PLANES = {'express': 1, 'taller': 4, 'pro': 10}

    @classmethod
    def validar_cupo_usuario(cls, empresa_actual):
        plan_codigo = getattr(empresa_actual, 'plan_activo', 'express') or 'express'
        limite_maximo = cls.LIMITES_PLANES.get(str(plan_codigo).lower(), 1)
        
        # Filtro estricto: solo Administrador y Vendedor
        usuarios_activos = get_user_model().objects.filter(
            empresa=empresa_actual,
            is_active=True
        ).filter(Q(rol__iexact='administrador') | Q(rol__iexact='vendedor')).count()
        
        return usuarios_activos < limite_maximo, usuarios_activos, limite_maximo
