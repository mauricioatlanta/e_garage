from dal import autocomplete
from dal_select2.widgets import ModelSelect2

from django import forms

from taller.models.clientes import Cliente
from taller.models.vehiculos import CajaVehiculo, Modelo, MotorVehiculo, Vehiculo


class VehiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.empresa = kwargs.pop("empresa", None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        empresa = self.empresa if self.empresa is not None else getattr(self.user, "empresa", None)

        if empresa:
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=empresa)
            country = getattr(empresa, "pais", "CL")
            self.fields["modelo"].queryset = Modelo.objects.filter(country=country)
            # Motores y cajas se cargan vía AJAX, iniciar vacíos
            self.fields["motor"].queryset = MotorVehiculo.objects.none()
            self.fields["caja"].queryset = CajaVehiculo.objects.none()
        else:
            # Si no hay user o empresa, no mostrar opciones
            self.fields["cliente"].queryset = Cliente.objects.none()
            self.fields["modelo"].queryset = Modelo.objects.none()
            self.fields["motor"].queryset = MotorVehiculo.objects.none()
            self.fields["caja"].queryset = CajaVehiculo.objects.none()

    class Meta:
        model = Vehiculo
        fields = [
            "cliente",
            "anio",
            "marca",
            "modelo",
            "motor",
            "caja",
            "patente",
            "vin",
            "color",
        ]
        widgets = {
            "cliente": autocomplete.ModelSelect2(
                url="autocomplete:cliente",
                attrs={
                    "data-placeholder": "🔍 Escribe el nombre del cliente para buscar...",
                    "data-minimum-input-length": 1,
                    "data-allow-clear": "true",
                    "style": "width:100%",
                },
            ),
            "marca": ModelSelect2(
                url="autocomplete:marca",
                attrs={
                    "data-placeholder": "Seleccionar marca...",
                    "data-minimum-input-length": 0,
                    "style": "width:100%",
                },
            ),
            "modelo": ModelSelect2(
                url="autocomplete:modelo",
                forward=["marca"],
                attrs={
                    "data-placeholder": "Modelos según marca...",
                    "data-minimum-input-length": 0,
                    "style": "width:100%",
                },
            ),
            "motor": ModelSelect2(
                url="vehiculos:motor-autocomplete",
                forward=["modelo"],
                attrs={
                    "data-placeholder": "Motor filtrado por modelo...",
                    "data-minimum-input-length": 0,
                    "style": "width:100%",
                },
            ),
            "caja": ModelSelect2(
                url="vehiculos:caja-autocomplete",
                forward=["modelo"],
                attrs={
                    "data-placeholder": "Caja filtrada por modelo...",
                    "data-minimum-input-length": 0,
                    "style": "width:100%",
                },
            ),
            "color": autocomplete.ModelSelect2(
                url="vehiculos:autocomplete_color",
                attrs={
                    "data-placeholder": "Selecciona o escribe un color...",
                    "data-tags": "true",  # Permite escribir uno nuevo
                    "data-allow-clear": "true",
                    "data-minimum-input-length": 0,
                    "style": "width:100%",
                },
            ),
        }
