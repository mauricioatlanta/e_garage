from allauth.account.forms import LoginForm
from allauth.account.adapter import get_adapter

from django import forms


class CustomLoginForm(LoginForm):
    """
    Formulario de login personalizado que permite login a superusuarios
    sin verificación de email
    """

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
        # Agregar clases CSS y atributos de accesibilidad a los campos existentes
        self.fields["login"].widget.attrs.update(
            {
                "class": "premium-input",
                "placeholder": "Usuario o email",
                "autocomplete": "username",
                "inputmode": "email",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "premium-input",
                "placeholder": "Contraseña",
                "autocomplete": "current-password",
                # Fix para iOS: Atributos específicos para evitar problemas de entrada
                "autocapitalize": "none",
                "autocorrect": "off",
                "spellcheck": "false",
                "inputmode": "text",
            }
        )

    def clean(self):
        """
        Validar formulario, pero permitir login a superusuarios sin verificación
        """
        # Llamar al clean del padre primero
        cleaned_data = super().clean()

        # Si hay un usuario y es superuser/staff, saltar verificación de email
        login = cleaned_data.get("login")
        if login:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            # Buscar usuario por username o email
            # Usar .first() en lugar de .get() para manejar múltiples usuarios con el mismo email
            user = None

            # Primero intentar buscar por username (más específico)
            user = User.objects.filter(username=login).first()

            # Si no se encuentra por username, buscar por email
            # Si hay múltiples usuarios con el mismo email, tomar el primero activo
            if not user:
                user = User.objects.filter(email=login, is_active=True).first()

            # Si es superuser o staff, permitir login sin verificación
            if user and (user.is_superuser or user.is_staff):
                # Forzar que el email se considere verificado
                if hasattr(user, "email") and user.email:
                    from allauth.account.models import EmailAddress

                    email_addr, _ = EmailAddress.objects.get_or_create(
                        user=user, email=user.email, defaults={"verified": True, "primary": True}
                    )
                    if not email_addr.verified:
                        email_addr.verified = True
                        email_addr.primary = True
                        email_addr.save()

        return cleaned_data

    def login(self, request, redirect_url=None):
        request.session.pop("empresa_id", None)
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
