# from dal.widgets import ModelSelect2Widget  # Temporarily disabled

from django import forms
from django.forms.widgets import Select

from taller.models.clientes import Cliente
from taller.models.region_ciudad import TallerCiudad, TallerRegion
from taller.models.ubicacion import Ciudad as CiudadUSA
from taller.models.ubicacion import Estado as EstadoUSA
from taller.utils.chile_locations import ensure_legacy_chile_locations


class ColorSelectWidget(Select):
    """Widget personalizado para mostrar colores con preview"""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)

        # Agregar atributo data-color si es un objeto ColorCliente
        if value and hasattr(self.choices.queryset.model, "codigo_color"):
            try:
                color_obj = self.choices.queryset.get(pk=value)
                option["attrs"]["data-color"] = color_obj.codigo_color
            except:
                pass

        return option


class CiudadChoiceField(forms.ModelChoiceField):
    """Campo personalizado que muestra solo el nombre de la ciudad sin el estado"""

    def label_from_instance(self, obj):
        return obj.nombre


class ClienteForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        empresa = self.empresa
        email = cleaned_data.get("email")
        if email and empresa:
            qs = Cliente.objects.filter(empresa=empresa, email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("email", "Ya existe un cliente con este email para esta empresa.")
        telefono = cleaned_data.get("telefono")
        if telefono and empresa:
            from django.core.exceptions import ValidationError

            from taller.utils.validators import validar_telefono

            try:
                telefono_normalizado = validar_telefono(telefono, self.pais)
            except ValidationError:
                telefono_normalizado = telefono

            qs = Cliente.objects.filter(empresa=empresa, telefono=telefono_normalizado)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("telefono", "Ya existe un cliente con este teléfono para esta empresa.")
        return cleaned_data

    # Campos para Chile
    region = forms.ModelChoiceField(
        queryset=TallerRegion.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                "id": "id_region",
                "class": "form-control",
                "data-param-name": "region_id",
            }
        ),
        empty_label="Seleccione Región",
    )
    ciudad = forms.ModelChoiceField(
        queryset=TallerCiudad.objects.none(),
        required=False,
        widget=forms.Select(attrs={"id": "id_ciudad", "class": "form-control"}),
        empty_label="Seleccione Ciudad",
    )

    # Campos para USA, Brasil, Venezuela, Perú (genérico usando modelo Estado/Ciudad)
    # Nota: Se reutilizan campos "estado_usa" y "ciudad_usa" para todos los países
    # que usan el modelo unificado Estado/Ciudad (US, BR, VE, PE)
    estado_usa = forms.ModelChoiceField(
        queryset=EstadoUSA.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                "id": "id_estado_usa",
                "class": "form-control",
                "data-param-name": "estado_id",
            }
        ),
        empty_label="Seleccione estado o departamento",
        label="Estado/Departamento",
    )
    ciudad_usa = CiudadChoiceField(
        queryset=CiudadUSA.objects.none(),
        required=False,
        widget=forms.Select(attrs={"id": "id_ciudad_usa", "class": "form-control"}),
        empty_label="Seleccione ciudad",
        label="Ciudad",
    )
    zipcode = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Código postal"}),
        label="Código Postal",
    )

    class Meta:
        model = Cliente
        fields = [
            "nombre",
            "apellido",
            "telefono",
            "direccion",
            "region",
            "ciudad",
            "estado_usa",
            "ciudad_usa",
            "zipcode",
            "email",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre"}),
            "apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellido"}),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+56912345678"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}
            ),
            "direccion": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Dirección"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)  # Almacenar empresa
        pais_override = kwargs.pop("pais", None)
        super().__init__(*args, **kwargs)

        # Solo nombre, apellido y teléfono son obligatorios (el modelo permite blank en apellido/teléfono).
        self.fields["nombre"].required = True
        self.fields["apellido"].required = True
        self.fields["telefono"].required = True
        self.fields["email"].required = False
        self.fields["direccion"].required = False

        # Agregar atributo pais para el template
        if pais_override:
            self.pais = pais_override
        elif self.empresa and hasattr(self.empresa, "pais"):
            self.pais = self.empresa.pais
        else:
            self.pais = "CL"  # Default a Chile
        self.pais = str(self.pais or "CL").upper()

        if self.pais == "CL" and (
            not TallerRegion.objects.exists() or not TallerCiudad.objects.exists()
        ):
            ensure_legacy_chile_locations()

        # Chile: región/ciudad
        if "region" in self.data and self.data.get("region") not in [None, ""]:
            try:
                region_id = int(self.data.get("region"))
                self.fields["ciudad"].queryset = TallerCiudad.objects.filter(region_id=region_id)
                if not self.fields["ciudad"].queryset.exists():
                    ensure_legacy_chile_locations(force=True)
                    self.fields["ciudad"].queryset = TallerCiudad.objects.filter(
                        region_id=region_id
                    )
            except (ValueError, TypeError):
                self.fields["ciudad"].queryset = TallerCiudad.objects.none()
        elif self.instance.pk and getattr(self.instance, "region", None):
            self.fields["ciudad"].queryset = TallerCiudad.objects.filter(
                region=self.instance.region
            )
            if not self.fields["ciudad"].queryset.exists():
                ensure_legacy_chile_locations(force=True)
                self.fields["ciudad"].queryset = TallerCiudad.objects.filter(
                    region=self.instance.region
                )
        else:
            self.fields["ciudad"].queryset = TallerCiudad.objects.none()

        self.fields["ciudad"].widget.attrs["data-selected"] = (
            self.data.get("ciudad")
            or (getattr(self.instance, "ciudad_id", None) if self.instance.pk else None)
            or ""
        )

        # USA, Brasil, Venezuela, Perú, Colombia, Ecuador: estado/ciudad/zipcode (usando modelo unificado)
        # Filtrar estados por país de la empresa
        estados_con_pais = ["US", "BR", "VE", "PE", "MX", "CO", "EC"]
        if self.pais in estados_con_pais:
            self.fields["estado_usa"].queryset = EstadoUSA.objects.filter(pais=self.pais).order_by(
                "nombre"
            )

        # Cargar ciudades si hay estado seleccionado
        if "estado_usa" in self.data and self.data.get("estado_usa") not in [None, ""]:
            try:
                estado_id = int(self.data.get("estado_usa"))
                self.fields["ciudad_usa"].queryset = CiudadUSA.objects.filter(
                    estado_id=estado_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["ciudad_usa"].queryset = CiudadUSA.objects.none()
        elif self.instance.pk and getattr(self.instance, "estado_usa", None):
            self.fields["ciudad_usa"].queryset = CiudadUSA.objects.filter(
                estado=self.instance.estado_usa
            ).order_by("nombre")
        else:
            self.fields["ciudad_usa"].queryset = CiudadUSA.objects.none()

        self.fields["ciudad_usa"].widget.attrs["data-selected"] = (
            self.data.get("ciudad_usa")
            or (getattr(self.instance, "ciudad_usa_id", None) if self.instance.pk else None)
            or ""
        )

        if not hasattr(self, "pais"):
            pais = None
            if self.empresa:
                pais = self.empresa.pais
            elif self.instance.pk and hasattr(self.instance, "empresa") and self.instance.empresa:
                pais = self.instance.empresa.pais
            self.pais = str(pais or "CL").upper()

        # Ocultar campos según el país
        if self.pais in estados_con_pais:
            # Países que usan modelo unificado Estado/Ciudad
            print(f"[DEBUG] [ClienteForm] Configurando campos para {self.pais} (Estado/Ciudad)")
            self.fields["region"].widget = forms.HiddenInput()
            self.fields["ciudad"].widget = forms.HiddenInput()

            etiqueta_estado = {
                "US": "Estado",
                "BR": "Estado",
                "VE": "Estado",
                "PE": "Departamento",
                "MX": "Estado",
            }.get(self.pais, "Estado")

            etiqueta_ciudad = {
                "BR": "Cidade",
            }.get(self.pais, "Ciudad")

            etiqueta_codigo = {
                "US": "Código Postal",
                "BR": "Código Postal",
                "VE": "Código Postal",
                "PE": "Código Postal",
                "MX": "Código Postal",
            }.get(self.pais, "Código Postal")

            self.fields["estado_usa"].label = etiqueta_estado
            self.fields["estado_usa"].empty_label = f"Seleccione {etiqueta_estado.lower()}"

            self.fields["ciudad_usa"].label = etiqueta_ciudad
            self.fields["ciudad_usa"].empty_label = f"Seleccione {etiqueta_ciudad.lower()}"

            self.fields["zipcode"].label = etiqueta_codigo
            self.fields["zipcode"].widget.attrs["placeholder"] = etiqueta_codigo
        else:
            # Chile usa modelo legacy Region/Ciudad
            print("[DEBUG] [ClienteForm] Configurando campos para Chile (Region/Ciudad)")
            self.fields["estado_usa"].widget = forms.HiddenInput()
            self.fields["ciudad_usa"].widget = forms.HiddenInput()
            self.fields["zipcode"].widget = forms.HiddenInput()

    def save(self, commit=True):
        obj = super().save(commit=False)

        if self.empresa and not obj.empresa_id:
            obj.empresa = self.empresa

        if commit:
            obj.save()
            self.save_m2m()
        return obj
