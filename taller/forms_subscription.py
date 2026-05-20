from django import forms
from django.core.exceptions import ValidationError
from .models import Empresa
from taller.services.plan_change_service import PlanLimitValidation

class PlanPagoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.empresa_actual = kwargs.pop('empresa_actual', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        
        if self.empresa_actual:
            # Desestructuramos la tupla de 3 elementos que devuelve tu servicio
            can_add, count, limite = PlanLimitValidation.can_add_user(self.empresa_actual)
            
            if not can_add:
                raise ValidationError(
                    f"Has alcanzado el límite de usuarios permitido para tu plan actual. "
                    f"Límite: {limite}, Actuales: {count}."
                )
                
        return cleaned_data

    class Meta:
        model = Empresa
        fields = ['plan']
