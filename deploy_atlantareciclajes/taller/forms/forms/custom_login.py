from allauth.account.forms import LoginForm

from django import forms


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
        # ✅ FASE REGISTRO: Campo único para email o celular
        self.fields["login"].label = "Email o Celular"
        self.fields["login"].widget.attrs.update(
            {
                "class": "premium-input",
                "placeholder": "Email o celular",
                "autocomplete": "username",
                "inputmode": "text",  # Cambiar a text para permitir números
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "premium-input",
                "placeholder": "Contraseña",
                "autocomplete": "current-password",
            }
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
