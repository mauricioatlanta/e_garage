# from dal.widgets import ModelSelect2Widget  # Temporarily disabled

from django import forms
from django.forms.widgets import Select

from taller.models.clientes import Cliente
from taller.models.color_cliente import ColorCliente
from taller.models.region_ciudad import TallerCiudad, TallerRegion
from taller.models.ubicacion import Ciudad as CiudadUSA
from taller.models.ubicacion import Estado as EstadoUSA


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


class ClienteForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        empresa = (
            self.initial.get("empresa") or self.instance.empresa
            if hasattr(self.instance, "empresa")
            else None
        )
        if email and empresa:
            qs = Cliente.objects.filter(empresa=empresa, email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("email", "Ya existe un cliente con este email para esta empresa.")
        return cleaned_data

    # Campos para Chile
    region = forms.ModelChoiceField(
        queryset=TallerRegion.objects.all(),
        required=False,
        widget=forms.Select(attrs={"id": "id_region", "class": "form-control"}),
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
        widget=forms.Select(attrs={"id": "id_estado_usa", "class": "form-control"}),
        empty_label="Select State / Estado / Departamento",
        label="Estado/Departamento",
    )
    ciudad_usa = forms.ModelChoiceField(
        queryset=CiudadUSA.objects.none(),
        required=False,
        widget=forms.Select(attrs={"id": "id_ciudad_usa", "class": "form-control"}),
        empty_label="Select City / Ciudad / Cidade",
        label="Ciudad/Cidade",
    )
    zipcode = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Zipcode / CEP / Código Postal"}
        ),
        label="Código Postal",
    )

    # Campo para color de identificación con autocomplete
    color = forms.ModelChoiceField(
        queryset=ColorCliente.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                "id": "id_color",
                "class": "form-control",
                "data-placeholder": "Seleccione Color",
                "data-allow-clear": "true",
                "data-minimum-input-length": 0,
            }
        ),
        help_text="Color para identificar al cliente/subscriptor",
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
            "color",
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
        super().__init__(*args, **kwargs)

        # Agregar atributo pais para el template
        if self.empresa and hasattr(self.empresa, "pais"):
            self.pais = self.empresa.pais
        else:
            self.pais = "CL"  # Default a Chile

        # Debug logging
        print(f"[DEBUG] [ClienteForm] empresa: {self.empresa}")
        if self.empresa:
            print(
                f"[DEBUG] [ClienteForm] empresa.pais: {getattr(self.empresa, 'pais', 'NO_HAY_PAIS')}"
            )
        else:
            print("[DEBUG] [ClienteForm] NO HAY EMPRESA")

        # Chile: región/ciudad
        if "region" in self.data and self.data.get("region") not in [None, ""]:
            try:
                region_id = int(self.data.get("region"))
                self.fields["ciudad"].queryset = TallerCiudad.objects.filter(region_id=region_id)
            except (ValueError, TypeError):
                self.fields["ciudad"].queryset = TallerCiudad.objects.none()
        elif self.instance.pk and getattr(self.instance, "region", None):
            self.fields["ciudad"].queryset = TallerCiudad.objects.filter(
                region=self.instance.region
            )
        else:
            self.fields["ciudad"].queryset = TallerCiudad.objects.none()

        # USA, Brasil, Venezuela, Perú: estado/ciudad/zipcode (usando modelo unificado)
        # Filtrar estados por país de la empresa
        if self.pais in ["US", "BR", "VE", "PE"]:
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

        # Exponer el país como atributo público para el template
        pais = None
        if self.empresa:
            pais = self.empresa.pais
        elif self.instance.pk and hasattr(self.instance, "empresa") and self.instance.empresa:
            pais = self.instance.empresa.pais
        self.pais = pais

        print(f"[DEBUG] [ClienteForm] pais detectado: {self.pais}")

        # Configurar colores según el país
        if self.pais:
            colores_disponibles = ColorCliente.get_colores_para_pais(self.pais)
            self.fields["color"].queryset = colores_disponibles
            print(
                f"[DEBUG] [ClienteForm] Colores disponibles para {self.pais}: {colores_disponibles.count()}"
            )
        else:
            # Fallback: mostrar todos los colores activos
            self.fields["color"].queryset = ColorCliente.objects.filter(activo=True)

        # Ocultar campos según el país
        if self.pais in ["US", "BR", "VE", "PE"]:
            # Países que usan modelo unificado Estado/Ciudad
            print(f"[DEBUG] [ClienteForm] Configurando campos para {self.pais} (Estado/Ciudad)")
            self.fields["region"].widget = forms.HiddenInput()
            self.fields["ciudad"].widget = forms.HiddenInput()

            # Personalizar labels según país
            if self.pais == "US":
                self.fields["estado_usa"].label = "State"
                self.fields["ciudad_usa"].label = "City"
                self.fields["zipcode"].label = "Zipcode"
            elif self.pais == "BR":
                self.fields["estado_usa"].label = "Estado"
                self.fields["ciudad_usa"].label = "Cidade"
                self.fields["zipcode"].label = "CEP"
            elif self.pais == "VE":
                self.fields["estado_usa"].label = "Estado"
                self.fields["ciudad_usa"].label = "Ciudad"
                self.fields["zipcode"].label = "Código Postal"
            elif self.pais == "PE":
                self.fields["estado_usa"].label = "Departamento"
                self.fields["ciudad_usa"].label = "Ciudad"
                self.fields["zipcode"].label = "Código Postal"
        else:
            # Chile usa modelo legacy Region/Ciudad
            print("[DEBUG] [ClienteForm] Configurando campos para Chile (Region/Ciudad)")
            self.fields["estado_usa"].widget = forms.HiddenInput()
            self.fields["ciudad_usa"].widget = forms.HiddenInput()
            self.fields["zipcode"].widget = forms.HiddenInput()

    def save(self, commit=True):
        obj = super().save(commit=False)

        # BLINDAJE MULTI-TENANT: SIEMPRE asignar empresa
        if self.empresa and not obj.empresa_id:
            obj.empresa = self.empresa

        if commit:
            obj.save()
            self.save_m2m()
        return obj
