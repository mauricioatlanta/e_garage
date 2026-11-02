from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from taller.services.plan_change_service import PlanLimitValidation

User = get_user_model()

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        # Capturamos la empresa que le pasaremos desde la vista
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean(self):
        cleaned_data = super().clean()
        
        # Si tenemos la empresa identificada, activamos el candado del plan
        if self.empresa:
            try:
                PlanLimitValidation.validar_cupo_usuario(self.empresa)
            except ValidationError as e:
                # Si el plan está lleno, levantamos el error directo al formulario
                raise forms.ValidationError(e.message)
        
        return cleaned_data
