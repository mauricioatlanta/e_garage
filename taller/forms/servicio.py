from django import forms

from taller.config.rubros import RUBROS_TALLER
from taller.servicios.models import Servicio


class ServicioForm(forms.ModelForm):
    # Permite elegir en qué rubro(s) se muestra. Si se deja vacío, CreateView lo llena con el rubro activo de la empresa.
    rubro_efectivo = forms.ChoiceField(
        choices=[("", "— Usar rubro de la empresa —")] + list(RUBROS_TALLER),
        required=False,
        label="Rubro",
        help_text="Si lo dejas vacío, queda con el rubro de tu empresa. Si eliges uno, solo se verá en ese rubro.",
    )
    class Meta:
        model = Servicio
        # Template espera subcategoria. Categoria se deriva de la subcategoria en form_valid del CBV.
        fields = ["nombre", "subcategoria", "rubro_efectivo"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.empresa = getattr(user, "empresa", None) if user else None
        # Label del dropdown en el idioma activo (en/es/pt), no siempre en es
        if "subcategoria" in self.fields:
            from django.utils.translation import get_language
            lang = (get_language() or "es")[:2]
            def _label(obj, _lang=lang):
                try:
                    return obj.get_label(_lang)
                except Exception:
                    return obj.code or str(obj)
            self.fields["subcategoria"].label_from_instance = _label
            self.fields["subcategoria"].label = "Subcategory" if lang == "en" else ("Subcategoria" if lang == "es" else "Subcategoria")
            self.fields["subcategoria"].required = True

    def clean(self):
        cleaned_data = super().clean()

        nombre = (cleaned_data.get("nombre") or "").strip()
        subcategoria = cleaned_data.get("subcategoria")
        categoria = cleaned_data.get("categoria") or (subcategoria.categoria if subcategoria else None)

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
