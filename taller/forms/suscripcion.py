from django import forms
from django.contrib.auth.models import User
from ..models.suscripcion import Suscripcion


class FormularioRegistro(forms.ModelForm):
    email = forms.EmailField()
    nombre = forms.CharField(max_length=100)
    nombre_taller = forms.CharField(max_length=255)
    telefono = forms.CharField(max_length=32)
    password = forms.CharField(widget=forms.PasswordInput)
    plan = forms.ChoiceField(choices=Suscripcion._meta.get_field('tipo').choices)


    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Suscripcion.objects.create(user=user, tipo=self.cleaned_data['plan'], activa=False)
            # TallerInfo se creará en la vista según el tipo de registro
        return user
