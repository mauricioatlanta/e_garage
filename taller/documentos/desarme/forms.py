# Formularios del módulo Desarme (vehículos tipo DESARME y piezas)

from django import forms

from taller.models.pieza_desarme import PiezaDesarme
from taller.models.vehiculos import Vehiculo


# Campos principales y opcionales para agrupar en templates
VEHICULO_DESARME_PRINCIPALES = [
    "patente",
    "vin",
    "marca",
    "modelo",
    "anio",
    "costo_adquisicion",
    "fecha_ingreso_desarme",
    "estado_desarme",
    "ubicacion_fisica",
    "observaciones_desarme",
]
VEHICULO_DESARME_OPCIONALES = [
    "marca_texto",
    "modelo_texto",
    "color",
    "motor",
    "caja",
]


class VehiculoDesarmeForm(forms.ModelForm):
    """Formulario para alta/edición de vehículos de desarme. tipo_uso=DESARME, sin cliente."""

    class Meta:
        model = Vehiculo
        fields = VEHICULO_DESARME_PRINCIPALES + VEHICULO_DESARME_OPCIONALES
        widgets = {
            "observaciones_desarme": forms.Textarea(attrs={"rows": 3, "class": "input-desarme"}),
            "patente": forms.TextInput(
                attrs={"placeholder": "Ej: ABCD12", "class": "input-desarme"}
            ),
            "vin": forms.TextInput(attrs={"placeholder": "Opcional", "class": "input-desarme"}),
            "estado_desarme": forms.TextInput(
                attrs={"placeholder": "Ej: En yarda, En proceso", "class": "input-desarme"}
            ),
            "ubicacion_fisica": forms.TextInput(
                attrs={"placeholder": "Ej: Fila 3, Pos 12", "class": "input-desarme"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        self.fields["vin"].required = False
        self.fields["costo_adquisicion"].required = False
        self.fields["fecha_ingreso_desarme"].required = False
        self.fields["estado_desarme"].required = False
        self.fields["ubicacion_fisica"].required = False
        self.fields["observaciones_desarme"].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo_uso = Vehiculo.TIPO_USO_DESARME
        instance.cliente = None
        if self.empresa:
            instance.empresa = self.empresa
        if commit:
            instance.save()
        return instance


PIEZA_DESARME_PRINCIPALES = [
    "vehiculo",
    "codigo",
    "nombre",
    "cantidad",
    "costo_asignado",
    "precio_venta_sugerido",
    "estado_pieza",
    "fecha_extraccion",
    "ubicacion_fisica",
    "observaciones",
]
PIEZA_DESARME_OPCIONALES = ["lado", "zona", "posicion"]


class PiezaDesarmeForm(forms.ModelForm):
    """Formulario para alta/edición de piezas de desarme."""

    class Meta:
        model = PiezaDesarme
        fields = PIEZA_DESARME_PRINCIPALES + PIEZA_DESARME_OPCIONALES
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 2, "class": "input-desarme"}),
            "costo_asignado": forms.NumberInput(attrs={"step": "0.01", "class": "input-desarme"}),
            "precio_venta_sugerido": forms.NumberInput(
                attrs={"step": "0.01", "class": "input-desarme"}
            ),
            "codigo": forms.TextInput(
                attrs={"placeholder": "Código interno o OEM", "class": "input-desarme"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        self.vehiculo = kwargs.pop("vehiculo", None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields["vehiculo"].queryset = Vehiculo.objects.filter(
                empresa=self.empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME
            ).order_by("patente", "vin")
        if self.vehiculo:
            self.fields["vehiculo"].initial = self.vehiculo
            self.fields["vehiculo"].disabled = True
        for f in (
            "fecha_extraccion",
            "ubicacion_fisica",
            "observaciones",
            "lado",
            "zona",
            "posicion",
        ):
            if f in self.fields:
                self.fields[f].required = False
