from allauth.account.forms import LoginForm
from django import forms
from django.contrib.auth import authenticate, login


class CustomLoginForm(LoginForm):
    remember_me = forms.BooleanField(
        label="Recordar credenciales",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "text-cyan-400 focus:ring-cyan-400 focus:ring-2",
                "id": "remember_me_checkbox",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases CSS a los campos existentes
        self.fields["login"].widget.attrs.update(
            {"class": "premium-input", "placeholder": "Usuario o email"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "premium-input", "placeholder": "Contraseña"}
        )

    def login(self, request, redirect_url=None):
        """
        Personalizar el login para manejar la funcionalidad "recordar"
        """
        ret = super().login(request, redirect_url)

        # Si el usuario marcó "recordar", extender la duración de la sesión
        if self.cleaned_data.get("remember_me"):
            # Configurar sesión para que dure 30 días
            request.session.set_expiry(60 * 60 * 24 * 30)  # 30 días
            # No expirar al cerrar el navegador
            request.session.cycle_key()
        else:
            # Configurar sesión normal (expira al cerrar navegador)
            request.session.set_expiry(0)

        return ret
