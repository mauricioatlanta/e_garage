from django import forms
from django.contrib.auth.models import User

from ..models.suscripcion import Suscripcion


class FormularioRegistro(forms.ModelForm):
    email = forms.EmailField(label="Email")
    nombre = forms.CharField(max_length=100, label="Name")
    nombre_taller = forms.CharField(max_length=255, label="Company")
    telefono = forms.CharField(max_length=32, label="Phone")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    plan = forms.ChoiceField(
        choices=[
            ("trial", "Free trial"),
            ("mensual", "Monthly"),
            ("semestral", "Semi-annual"),
            ("anual", "Annual"),
        ],
        label="Plan",
    )
    pais = forms.ChoiceField(
        choices=[
            ("US", "United States"),
            ("CL", "Chile"),
            ("MX", "México"),
            ("PE", "Perú"),
            ("CO", "Colombia"),
            ("EC", "Ecuador"),
            ("BR", "Brasil"),
            ("VE", "Venezuela"),
        ],
        initial="US",
        label="Country",
        help_text="Select your country to configure currency and regional settings",
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Ya existe un usuario con este email. Por favor, usa un email diferente."
            )
        return email

    def __init__(self, *args, **kwargs):
        # Extraer request de kwargs antes de llamar a super()
        request = kwargs.pop("request", None)

        # Detectar país automáticamente desde la URL usando CountrySettings
        from taller.config.country_settings import CountrySettings

        detected_country = None
        if request:
            detected_country = CountrySettings.get_country_from_url(request.path)

        # Modificar datos antes de super() si hay país detectado
        if request and args and hasattr(args[0], "copy") and detected_country:
            data = args[0].copy()
            data["pais"] = detected_country
            args = (data,) + args[1:]

        super().__init__(*args, **kwargs)

        # Configurar el campo después de super() usando país detectado
        if request and detected_country:
            # Ocultar campo si el país se detecta automáticamente desde URL
            self.fields["pais"].initial = detected_country
            self.fields["pais"].widget = forms.HiddenInput()

        # El campo username se maneja completamente en el método save()

    class Meta:
        model = User
        fields = ["email", "password"]  # Remover username de los campos
        labels = {
            "email": "Email",
        }

    def save(self, commit=True):
        user = super().save(commit=False)

        # Generar username único basado en el email
        email = self.cleaned_data["email"]
        base_username = email.split("@")[0]  # Parte antes del @
        username = base_username

        # Si el username ya existe, agregar un número
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user.username = username
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            Suscripcion.objects.create(user=user, tipo=self.cleaned_data["plan"], activa=False)
            # TallerInfo se creará en la vista según el tipo de registro
        return user
