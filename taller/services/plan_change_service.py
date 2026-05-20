from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

class PlanLimitValidation:
    LIMITES_PLANES = {
        'express': 1,
        'taller': 4,
        'pro': 10
    }

    @classmethod
    def validar_cupo_usuario(cls, empresa_actual):
        # Intentamos obtener el plan. Si no tiene o falla, asumimos 'express' (1 usuario)
        plan_codigo = getattr(empresa_actual, 'plan_activo', 'express') or 'express'
        limite_maximo = cls.LIMITES_PLANES.get(str(plan_codigo).lower(), 1)

        # Contamos cuántos usuarios administrativos activos tiene la empresa hoy
        usuarios_activos = User.objects.filter(
            empresa=empresa_actual, 
            is_active=True
        ).count()

        if usuarios_activos >= limite_maximo:
            raise ValidationError(
                f"Límite alcanzado. Tu plan '{plan_codigo.upper()}' "
                f"solo permite {limite_maximo} usuario(s) administrativo(s)."
            )
