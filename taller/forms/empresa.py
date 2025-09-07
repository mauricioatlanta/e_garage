from django import forms

from taller.models.empresa import Empresa


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["nombre_taller", "empresa", "logo", "direccion", "telefono"]
        widgets = {
            "nombre_taller": forms.TextInput(
                attrs={
                    "class": "futuristic-input w-full",
                    "placeholder": "Nombre de tu taller",
                }
            ),
            "empresa": forms.TextInput(
                attrs={
                    "class": "futuristic-input w-full",
                    "placeholder": "Nombre de la empresa/compañía",
                }
            ),
            "direccion": forms.TextInput(
                attrs={
                    "class": "futuristic-input w-full",
                    "placeholder": "Dirección del taller",
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "futuristic-input w-full",
                    "placeholder": "+56 9 1234 5678",
                }
            ),
            "logo": forms.FileInput(
                attrs={"class": "futuristic-input w-full", "accept": "image/*"}
            ),
        }
        labels = {
            "nombre_taller": "🏢 Nombre del Taller",
            "empresa": "🏭 Empresa/Compañía",
            "logo": "🖼️ Logo del Taller",
            "direccion": "📍 Dirección",
            "telefono": "📞 Teléfono",
        }


class DatosPersonalesForm(forms.Form):
    """Formulario para datos personales del usuario"""

    first_name = forms.CharField(
        max_length=30,
        label="👤 Nombre",
        widget=forms.TextInput(
            attrs={"class": "futuristic-input w-full", "placeholder": "Tu nombre"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        label="👤 Apellido",
        widget=forms.TextInput(
            attrs={"class": "futuristic-input w-full", "placeholder": "Tu apellido"}
        ),
    )
    email = forms.EmailField(
        label="📧 Email",
        widget=forms.EmailInput(
            attrs={"class": "futuristic-input w-full", "placeholder": "tu@email.com"}
        ),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
