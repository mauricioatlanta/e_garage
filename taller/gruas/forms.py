from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from taller.models import Cliente, TowingDriver, TowingLedgerEntry, TowingOrder, TowingUnit


class TowingOrderForm(forms.ModelForm):
    class Meta:
        model = TowingOrder
        fields = [
            "solicitante", "patente_snapshot", "vehiculo_snapshot", "pagador_nombre",
            "receptor_nombre", "origen", "destino", "planned_start_at", "planned_end_at",
        ]
        widgets = {"planned_start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}), "planned_end_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["solicitante"].queryset = Cliente.objects.filter(empresa=empresa) if empresa else Cliente.objects.none()


class TowingQuoteForm(forms.Form):
    net_amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=14, decimal_places=2)
    tax_rate = forms.DecimalField(min_value=Decimal("0"), max_value=Decimal("100"), decimal_places=2, initial=Decimal("19.00"))
    included_km = forms.DecimalField(min_value=Decimal("0"), decimal_places=2, required=False, initial=Decimal("0"))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class TowingLedgerForm(forms.Form):
    entry_type = forms.ChoiceField(choices=TowingLedgerEntry.ENTRY_CHOICES)
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=14, decimal_places=2)
    reference = forms.CharField(required=False)


class TowingAssignmentForm(forms.Form):
    unit = forms.ModelChoiceField(queryset=TowingUnit.objects.none())
    driver = forms.ModelChoiceField(queryset=TowingDriver.objects.none())
    planned_start_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    planned_end_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields["unit"].queryset = TowingUnit.objects.filter(empresa=empresa, estado="ACTIVA")
            self.fields["driver"].queryset = TowingDriver.objects.filter(empresa=empresa, activo=True)


class TowingEvidenceForm(forms.Form):
    """Photo evidence submitted by a driver from the mobile workflow."""

    MAX_SIZE = 10 * 1024 * 1024
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    KIND_CHOICES = (
        ("RETIRO", "Foto de retiro"),
        ("ENTREGA", "Foto de entrega"),
        ("DANOS", "Daños observados"),
        ("GENERAL", "Otra evidencia"),
    )

    file = forms.ImageField(
        label="Foto",
        help_text="JPG, PNG o WebP; máximo 10 MB.",
    )
    kind = forms.ChoiceField(label="Tipo de evidencia", choices=KIND_CHOICES)
    description = forms.CharField(label="Descripción", required=False, max_length=500)

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if uploaded.size > self.MAX_SIZE:
            raise ValidationError("La foto no puede superar 10 MB.")
        content_type = (getattr(uploaded, "content_type", "") or "").lower()
        if content_type not in self.ALLOWED_TYPES:
            raise ValidationError("Solo se aceptan fotos JPG, PNG o WebP.")
        return uploaded
