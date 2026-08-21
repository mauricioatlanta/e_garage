from django import forms

from taller.servicios.models import Servicio


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ["nombre", "categoria"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.empresa = getattr(user, "empresa", None) if user else None

    def clean(self):
        cleaned_data = super().clean()

        nombre = (cleaned_data.get("nombre") or "").strip()
        categoria = cleaned_data.get("categoria")

        if self.empresa and nombre and categoria:
            qs = Servicio.objects.filter(
                empresa=self.empresa,
                nombre=nombre,
                categoria=categoria,
            )

            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "Ya existe un servicio con este nombre en esta categoría."
                )

        return cleaned_data
