from django import forms
from django.forms import BaseFormSet, formset_factory

from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)
from taller.models.repuesto import Repuesto
from taller.servicios.models import Servicio


# Formset para repuestos
class RepuestoForm(forms.ModelForm):
    class Meta:
        model = LineaRepuesto
        fields = [
            "repuesto",
            "codigo",
            "nombre",
            "cantidad",
            "precio_unitario",
            "descuento",
        ]
        widgets = {
            "repuesto": forms.Select(attrs={"class": "form-select rep-repuesto"}),
            "codigo": forms.TextInput(
                attrs={"class": "form-control rep-codigo", "placeholder": "Código"}
            ),
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control rep-nombre",
                    "placeholder": "Nombre del repuesto",
                }
            ),
            "cantidad": forms.NumberInput(
                attrs={"class": "form-control rep-cantidad", "min": "1", "step": "1"}
            ),
            "precio_unitario": forms.TextInput(
                attrs={
                    "class": "form-control rep-precio-venta",
                    "placeholder": "$0.00",
                    "inputmode": "decimal",
                }
            ),
            "descuento": forms.NumberInput(
                attrs={
                    "class": "form-control rep-descuento",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        if self.empresa:
            self.fields["repuesto"].queryset = Repuesto.objects.filter(
                empresa=self.empresa
            )


RepuestoFormSet = formset_factory(
    RepuestoForm, extra=0, can_delete=True, min_num=1, validate_min=True, formset=BaseFormSet
)


# Formset para servicios
class ServicioForm(forms.ModelForm):
    class Meta:
        model = LineaServicio
        fields = ["servicio", "nombre", "cantidad", "precio_unitario", "descuento"]
        widgets = {
            "servicio": forms.Select(attrs={"class": "form-select serv-servicio"}),
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control serv-nombre",
                    "placeholder": "Nombre del servicio",
                }
            ),
            "cantidad": forms.NumberInput(
                attrs={"class": "form-control serv-cantidad", "min": "1", "step": "1"}
            ),
            "precio_unitario": forms.TextInput(
                attrs={
                    "class": "form-control serv-precio-unitario",
                    "placeholder": "$0.00",
                    "inputmode": "decimal",
                }
            ),
            "descuento": forms.NumberInput(
                attrs={
                    "class": "form-control serv-descuento",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        if self.empresa:
            self.fields["servicio"].queryset = Servicio.objects.filter(
                empresa=self.empresa
            )


ServicioFormSet = formset_factory(
    ServicioForm, extra=0, can_delete=True, formset=BaseFormSet
)


# Formset para otros servicios
class OtroServicioForm(forms.ModelForm):
    class Meta:
        model = LineaOtroServicio
        fields = [
            "servicio",
            "nombre",
            "empresa_externa",
            "cantidad",
            "costo_interno",
            "precio_cliente",
        ]
        widgets = {
            "servicio": forms.Select(attrs={"class": "form-select otr-servicio"}),
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control otr-nombre",
                    "placeholder": "Nombre del servicio externo",
                }
            ),
            "empresa_externa": forms.TextInput(
                attrs={
                    "class": "form-control otr-empresa",
                    "placeholder": "Empresa externa",
                }
            ),
            "cantidad": forms.NumberInput(
                attrs={"class": "form-control otr-cantidad", "min": "1", "step": "1"}
            ),
            "costo_interno": forms.TextInput(
                attrs={
                    "class": "form-control otr-costo",
                    "placeholder": "$0.00",
                    "inputmode": "decimal",
                }
            ),
            "precio_cliente": forms.TextInput(
                attrs={
                    "class": "form-control otr-precio",
                    "placeholder": "$0.00",
                    "inputmode": "decimal",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        if self.empresa:
            self.fields["servicio"].queryset = Servicio.objects.filter(
                empresa=self.empresa
            )


OtroServicioFormSet = formset_factory(
    OtroServicioForm, extra=0, can_delete=True, formset=BaseFormSet
)


def guardar_formset(formset, doc, empresa, user):
    """
    Guarda líneas amarrándolas al documento/empresa y completando auditoría.
    Aplica reglas básicas; reglas de IVA/sales tax deben ir en los forms o servicios.
    """
    if not formset.is_valid():
        return False
    saved_any = False
    for form in formset:
        if not getattr(form, "cleaned_data", None) or form.cleaned_data.get("DELETE"):
            continue
        obj = form.save(commit=False)
        # Multi-tenant & herencia básica
        if hasattr(obj, "documento"):
            obj.documento = doc
        if hasattr(obj, "empresa"):
            obj.empresa = empresa
        if hasattr(obj, "created_by") and not getattr(obj, "pk", None):
            obj.created_by = user
        if hasattr(obj, "updated_by"):
            obj.updated_by = user
        obj.save()
        saved_any = True
    return saved_any
