from django import forms

from taller.models.ubicacion import Ciudad, Estado
from utils.pais import get_ciudades, get_regiones


class SignupChileForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    username = forms.CharField(label="Nombre de usuario")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Repite tu contraseña", widget=forms.PasswordInput
    )
    region = forms.ChoiceField(label="Región", choices=[], required=True)
    ciudad = forms.ChoiceField(label="Ciudad", choices=[], required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["region"].choices = [(r, r) for r in get_regiones("CL")]
        region = self.data.get("region") or (
            self.initial.get("region") if self.initial else None
        )
        if region:
            self.fields["ciudad"].choices = [(c, c) for c in get_ciudades("CL", region)]
        else:
            self.fields["ciudad"].choices = [("", "---------")]


class SignupUSAForm(forms.Form):
    email = forms.EmailField(label="Email")
    username = forms.CharField(label="Username")
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repeat password", widget=forms.PasswordInput)
    state = forms.ChoiceField(label="State", choices=[], required=True)
    city = forms.ChoiceField(label="City", choices=[], required=True)
    zipcode = forms.CharField(label="Zip Code", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener queryset de estados
        estados = Estado.objects.all().order_by("nombre")
        self.fields["state"].choices = [(e.pk, e.nombre) for e in estados]
        state_id = self.data.get("state") or (
            self.initial.get("state") if self.initial else None
        )
        if state_id:
            ciudades = Ciudad.objects.filter(estado_id=state_id).order_by("nombre")
            choices = [(c.pk, c.nombre) for c in ciudades]
            choices.append(("otra", "Otra"))
            choices.append(("other", "Other"))
            self.fields["city"].choices = choices
        else:
            self.fields["city"].choices = [
                ("", "---------"),
                ("otra", "Otra"),
                ("other", "Other"),
            ]
