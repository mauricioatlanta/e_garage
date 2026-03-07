"""
Formularios para el flujo de Centro de Ingreso Pro (ops/ingreso).
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from taller.utils.ocr import normalizar_patente


class PatenteForm(forms.Form):
    patente = forms.CharField(
        max_length=20,
        label=_("Patente"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "ABCD12", "autofocus": True}
        ),
    )

    def clean_patente(self):
        value = self.cleaned_data.get("patente")
        if value:
            return normalizar_patente(value)
        return value


class KilometrajeForm(forms.Form):
    kilometraje = forms.IntegerField(
        min_value=0,
        label=_("Kilometraje"),
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    )
    foto_tablero = forms.ImageField(
        required=False,
        label=_("Foto tablero"),
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )
    omitido_motivo = forms.CharField(
        max_length=255,
        required=False,
        label=_("Motivo si omite foto"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Ej: tablero no visible")}
        ),
    )
    confirmar_km_menor = forms.BooleanField(
        required=False,
        label=_("Confirmo que el kilometraje es correcto (menor al anterior)"),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean(self):
        data = super().clean()
        foto = data.get("foto_tablero")
        motivo = (data.get("omitido_motivo") or "").strip()
        if not foto and not motivo:
            raise forms.ValidationError(
                _("Debe subir foto del tablero o indicar motivo de omisión.")
            )
        return data


class DocumentoIngresoForm(forms.Form):
    TIPO_CHOICES = [
        ("OT", _("Orden de Trabajo")),
        ("PRES", _("Presupuesto")),
    ]
    motivo = forms.CharField(
        required=False,
        label=_("Motivo ingreso"),
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 2, "placeholder": _("Ej: Revisión frenos")}
        ),
    )
    tipo_documento = forms.ChoiceField(
        choices=TIPO_CHOICES,
        label=_("Tipo documento"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class VehiculoQuickCreateForm(forms.Form):
    patente = forms.CharField(
        max_length=20,
        label=_("Patente"),
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
    )
    cliente = forms.ModelChoiceField(
        queryset=None,
        label=_("Cliente"),
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )
    marca_texto = forms.CharField(
        max_length=100,
        required=False,
        label=_("Marca"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("Opcional")}),
    )
    modelo_texto = forms.CharField(
        max_length=150,
        required=False,
        label=_("Modelo"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("Opcional")}),
    )
    anio = forms.IntegerField(
        min_value=1900,
        max_value=2100,
        label=_("Año"),
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            from taller.models import Cliente

            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=empresa).order_by(
                "nombre", "apellido"
            )


class ChecklistIngresoForm(forms.Form):
    nivel_combustible = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=0,
        label=_("Nivel combustible (0-100)"),
        widget=forms.NumberInput(
            attrs={"class": "form-control", "type": "range", "min": 0, "max": 100}
        ),
    )
    luces_funcionan = forms.BooleanField(
        initial=True,
        label=_("Luces funcionan"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    objetos_valor = forms.CharField(
        required=False,
        label=_("Objetos de valor"),
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 2, "placeholder": _("Descripción o ninguno")}
        ),
    )
    foto_frontal = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"accept": "image/*"})
    )
    foto_trasera = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"accept": "image/*"})
    )
    foto_lateral_1 = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"accept": "image/*"})
    )
    foto_lateral_2 = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"accept": "image/*"})
    )
