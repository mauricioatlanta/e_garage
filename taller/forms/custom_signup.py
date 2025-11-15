from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class CustomSignupForm(UserCreationForm):
    """
    Formulario de registro personalizado con selección de país
    """

    COUNTRY_CHOICES = [
        ("CL", "🇨🇱 Chile"),
        ("US", "🇺🇸 United States"),
        ("MX", "🇲🇽 México"),
    ]

    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={"class": "input-futurista", "id": "id_country"}),
        label="Country / País",
        required=True,
        initial="US",  # Por defecto USA
    )

    class Meta:
        model = User
        fields = ("email", "username", "password1", "password2", "country")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer email requerido
        self.fields["email"].required = True
        self.fields["email"].widget.attrs.update(
            {"class": "input-futurista", "placeholder": "your@email.com"}
        )
        self.fields["username"].widget.attrs.update(
            {"class": "input-futurista", "placeholder": "username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "input-futurista", "placeholder": "••••••••"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "input-futurista", "placeholder": "••••••••"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
