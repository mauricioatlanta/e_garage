from datetime import date

from django import forms

from taller.models.clientes import Cliente
from taller.models.marca import Marca
from taller.models.vehiculos import CajaVehiculo, Modelo, MotorVehiculo, Vehiculo


class VehiculoFormSimple(forms.ModelForm):
    # Campo año dinámico
    anio = forms.TypedChoiceField(
        coerce=int,
        choices=[
            (y, y) for y in range(date.today().year + 1, 1969, -1)
        ],  # 1970 → año actual + 1
        required=True,
        label="Año",
    )

    # Campos motor y caja que empiezan vacíos
    motor = forms.ModelChoiceField(
        queryset=MotorVehiculo.objects.none(),
        required=False,
        label="Motor",
    )
    caja = forms.ModelChoiceField(
        queryset=CajaVehiculo.objects.none(),
        required=False,
        label="Caja",
    )

    def __init__(self, *args, **kwargs):
        # BLINDAJE MULTI-TENANT: Extraer user y filtrar por empresa
        self.user = kwargs.pop("user", None)
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, "empresa"):
            # Filtrar clientes por empresa del usuario
            self.fields["cliente"].queryset = Cliente.objects.filter(
                empresa=self.user.empresa
            )
            # Filtrar marcas por país de la empresa
            country = getattr(self.user.empresa, "pais", "CL")
            self.fields["marca"].queryset = Marca.objects.filter(country=country)
            # Inicialmente no mostrar modelos hasta que se seleccione una marca
            # Modelo NO tiene campo empresa, solo country
            self.fields["modelo"].queryset = Modelo.objects.none()
            # Motor y caja empiezan vacíos - se llenan solo si hay modelo seleccionado
            self.fields["motor"].queryset = MotorVehiculo.objects.none()
            self.fields["caja"].queryset = CajaVehiculo.objects.none()
        else:
            # Si no hay user o empresa, no mostrar opciones
            self.fields["cliente"].queryset = Cliente.objects.none()
            self.fields["marca"].queryset = Marca.objects.none()
            self.fields["modelo"].queryset = Modelo.objects.none()
            self.fields["motor"].queryset = MotorVehiculo.objects.none()
            self.fields["caja"].queryset = CajaVehiculo.objects.none()

        # Si viene marca en POST (o GET al recargar con errores), filtrar modelos por marca
        marca_id = (
            self.data.get("marca")
            or self.initial.get("marca")
            or (self.instance.marca_id if getattr(self.instance, "pk", None) else None)
        )
        anio_val = (
            self.data.get("anio")
            or self.initial.get("anio")
            or (self.instance.anio if getattr(self.instance, "pk", None) else None)
        )

        if marca_id and self.empresa:
            # Filtrar modelos por marca seleccionada
            country = getattr(self.empresa, "pais", "CL")
            qs = Modelo.objects.filter(marca_id=marca_id, country=country)

            # Si el modelo tiene relación con año, aplica filtro:
            # (Nota: Modelo no tiene campo año directo, pero podrías agregarlo si necesitas)
            # if anio_val and hasattr(Modelo, "anio"):
            #     qs = qs.filter(anio=anio_val)

            self.fields["modelo"].queryset = qs.order_by("nombre")
        else:
            # vacío para evitar "choices" erróneas
            self.fields["modelo"].queryset = Modelo.objects.none()

        # Si viene modelo en POST (o GET al recargar con errores), filtra dinámicamente
        modelo_id = (
            self.data.get("modelo")
            or self.initial.get("modelo")
            or (self.instance.modelo_id if getattr(self.instance, "pk", None) else None)
        )

        if modelo_id and self.empresa:
            # Filtrar motores y cajas por modelo (usando ManyToMany)
            self.fields["motor"].queryset = MotorVehiculo.objects.filter(
                modelos__id=modelo_id
            ).distinct()
            self.fields["caja"].queryset = CajaVehiculo.objects.filter(
                modelos__id=modelo_id
            ).distinct()

    def clean(self):
        """Validación server-side para asegurar que motor/caja pertenezcan al modelo"""
        cleaned_data = super().clean()
        modelo = cleaned_data.get("modelo")
        motor = cleaned_data.get("motor")
        caja = cleaned_data.get("caja")

        if modelo and motor:
            # Verificar que el motor pertenezca al modelo
            if not motor.modelos.filter(id=modelo.id).exists():
                self.add_error(
                    "motor", "El motor no corresponde al modelo seleccionado."
                )

        if modelo and caja:
            # Verificar que la caja pertenezca al modelo
            if not caja.modelos.filter(id=modelo.id).exists():
                self.add_error("caja", "La caja no corresponde al modelo seleccionado.")

        return cleaned_data

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
            "cliente": forms.Select(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "id": "id_cliente",
                }
            ),
            "marca": forms.Select(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "id": "id_marca",
                }
            ),
            "modelo": forms.Select(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "id": "id_modelo",
                }
            ),
            "motor": forms.Select(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "id": "id_motor",
                }
            ),
            "caja": forms.Select(
                attrs={
                    "class": "form-control",
                    "style": "width:100%",
                    "id": "id_caja",
                }
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
