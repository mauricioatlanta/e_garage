from django import forms
from utils.pais import get_regiones, get_ciudades

class SignupChileForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    username = forms.CharField(label='Nombre de usuario')
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repite tu contraseña', widget=forms.PasswordInput)
    region = forms.ChoiceField(label='Región', choices=[], required=True)
    ciudad = forms.ChoiceField(label='Ciudad', choices=[], required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].choices = [(r, r) for r in get_regiones('CL')]
        region = self.data.get('region') or (self.initial.get('region') if self.initial else None)
        if region:
            self.fields['ciudad'].choices = [(c, c) for c in get_ciudades('CL', region)]
        else:
            self.fields['ciudad'].choices = [('', '---------')]

class SignupUSAForm(forms.Form):
    email = forms.EmailField(label='Email')
    username = forms.CharField(label='Username')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    state = forms.ChoiceField(label='State', choices=[], required=True)
    city = forms.ChoiceField(label='City', choices=[], required=True)
    zipcode = forms.CharField(label='Zip Code', required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'].choices = [(r, r) for r in get_regiones('US')]
        state = self.data.get('state') or (self.initial.get('state') if self.initial else None)
        if state:
            self.fields['city'].choices = [(c, c) for c in get_ciudades('US', state)]
        else:
            self.fields['city'].choices = [('', '---------')]
