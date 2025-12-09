from dal import autocomplete

from django import forms

from taller.models.clientes import Cliente
from taller.models.marca import Marca
from taller.models.vehiculos import CajaVehiculo, Modelo, MotorVehiculo, Vehiculo


class VehiculoFormDAL(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # Filtrar por empresa/tenant
        if self.empresa:
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=self.empresa)
            # Determinar país basado en la empresa
            country = getattr(self.empresa, "pais", "CL")
            self.fields["marca"].queryset = Marca.objects.filter(country=country)
            self.fields["modelo"].queryset = Modelo.objects.filter(country=country)
            self.fields["motor"].queryset = (
                MotorVehiculo.objects.all()
            )  # Motor no tiene campo empresa
            self.fields["caja"].queryset = CajaVehiculo.objects.all()  # Caja no tiene campo empresa
        else:
            self.fields["cliente"].queryset = Cliente.objects.none()
            self.fields["marca"].queryset = Marca.objects.none()
            self.fields["modelo"].queryset = Modelo.objects.none()
            self.fields["motor"].queryset = MotorVehiculo.objects.none()
            self.fields["caja"].queryset = CajaVehiculo.objects.none()

        # Prefijo país/idioma para rutas absolutas (evita reverse())
        prefix = "/cl/es/"
        if request and request.path.startswith("/us/"):
            prefix = "/us/"

        # Cliente
        self.fields["cliente"].widget.url = None
        self.fields["cliente"].widget.attrs.update(
            {
                "data-ajax--url": f"{prefix}clientes/autocomplete/",
                "data-placeholder": "🔍 Escribe el nombre del cliente…",
                "data-minimum-input-length": 1,
                "data-allow-clear": "true",
                "style": "width:100%",
            }
        )

        # Modelo (forward al campo 'marca')
        self.fields["modelo"].widget.url = None
        # asegura forward si no lo definiste en la declaración del field
        if not getattr(self.fields["modelo"].widget, "forward", None):
            self.fields["modelo"].widget.forward = ["marca"]
        self.fields["modelo"].widget.attrs.update(
            {
                "data-ajax--url": f"{prefix}vehiculos/autocomplete/modelo/",
                "data-placeholder": "Modelo…",
                "style": "width:100%",
            }
        )

        # Motor (forward al campo 'modelo')
        self.fields["motor"].widget.url = None
        # asegura forward si no lo definiste en la declaración del field
        if not getattr(self.fields["motor"].widget, "forward", None):
            self.fields["motor"].widget.forward = ["modelo"]
        self.fields["motor"].widget.attrs.update(
            {
                "data-ajax--url": f"{prefix}vehiculos/autocomplete/motor-por-modelo/",
                "data-placeholder": "Motor…",
                "style": "width:100%",
            }
        )

        # Caja (forward al campo 'modelo')
        self.fields["caja"].widget.url = None
        if not getattr(self.fields["caja"].widget, "forward", None):
            self.fields["caja"].widget.forward = ["modelo"]
        self.fields["caja"].widget.attrs.update(
            {
                "data-ajax--url": f"{prefix}vehiculos/autocomplete/caja-por-modelo/",
                "data-placeholder": "Caja…",
                "style": "width:100%",
            }
        )

        # Año - se llena con JavaScript

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
                url=None,
                attrs={
                    "style": "width:100%",
                    "data-placeholder": "🔍 Escribe el nombre del cliente para buscar...",
                    "data-minimum-input-length": 1,
                    "data-allow-clear": "true",
                },
            ),
            "marca": forms.Select(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "id": "id_marca",
                }
            ),
            "modelo": autocomplete.ModelSelect2(
                url=None,
                forward=["marca"],
                attrs={
                    "style": "width:100%",
                    "data-placeholder": "Seleccionar modelo...",
                    "data-minimum-input-length": 0,
                },
            ),
            "motor": autocomplete.ModelSelect2(
                url=None,
                forward=["modelo"],
                attrs={
                    "style": "width:100%",
                    "data-placeholder": "Motor filtrado por modelo...",
                    "data-minimum-input-length": 0,
                },
            ),
            "caja": autocomplete.ModelSelect2(
                url=None,
                forward=["modelo"],
                attrs={
                    "style": "width:100%",
                    "data-placeholder": "Caja filtrada por modelo...",
                    "data-minimum-input-length": 0,
                },
            ),
            "color": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "placeholder": "Ej: Rojo, Azul, Blanco...",
                    "id": "id_color",
                }
            ),
            "anio": forms.Select(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "id": "id_anio",
                }
            ),
            "patente": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "placeholder": "Ej: ABCD12",
                    "id": "id_patente",
                }
            ),
            "vin": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "placeholder": "VIN (17 caracteres)",
                    "maxlength": "17",
                    "minlength": "17",
                    "id": "id_vin",
                }
            ),
        }
