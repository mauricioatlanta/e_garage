from dal import autocomplete
from dal_select2.widgets import ModelSelect2

from django import forms

from taller.models.clientes import Cliente
from taller.models.vehiculos import CajaVehiculo, Modelo, MotorVehiculo, Vehiculo


class VehiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # BLINDAJE MULTI-TENANT: Extraer user y filtrar por empresa
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, "empresa"):
            # Filtrar clientes por empresa del usuario
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=self.user.empresa)
            # Filtrar modelos por país de la empresa
            country = getattr(self.user.empresa, "pais", "CL")
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
