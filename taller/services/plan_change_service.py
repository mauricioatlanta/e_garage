from django.contrib.auth import get_user_model
from django.db.models import Q

class PlanLimitValidation:
    LIMITES_PLANES = {'express': 1, 'taller': 4, 'pro': 10}

    @classmethod
    def get_count(cls, empresa):
        return get_user_model().objects.filter(
            empresa=empresa, 
            is_active=True
        ).filter(
            Q(rol__iexact='administrador') | Q(rol__iexact='vendedor')
        ).count()

    @classmethod
    def can_add_user(cls, empresa):
        limite = cls.LIMITES_PLANES.get(empresa.plan, 1)
        count = cls.get_count(empresa)
        return count < limite, count, limite
