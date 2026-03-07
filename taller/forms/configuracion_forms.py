from django import forms

from taller.models import ConfiguracionEmpresa


class CompanyInfoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            "logo",
            "nombre_publico",
            "tagline",
            "direccion",
            "telefono",
            "email_contacto",
            "tasa_impuesto",
            "aplicar_impuesto_por_defecto",
        ]
        widgets = {
            "direccion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Dirección completa de su empresa",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estilos opcionales
        self.fields["logo"].widget.attrs.update({"class": "form-control", "accept": "image/*"})
        self.fields["nombre_publico"].widget.attrs.update({"class": "form-control"})
        self.fields["tagline"].widget.attrs.update({"class": "form-control"})
        self.fields["telefono"].widget.attrs.update(
            {"class": "form-control", "placeholder": "+56 9 1234 5678"}
        )
        self.fields["email_contacto"].widget.attrs.update(
            {"class": "form-control", "placeholder": "contacto@suempresa.com"}
        )
        self.fields["tasa_impuesto"].widget.attrs.update({"class": "form-control"})
        self.fields["aplicar_impuesto_por_defecto"].widget.attrs.update(
            {"class": "form-check-input"}
        )

        # Hacer que tasa_impuesto no sea requerido y tenga valor por defecto
        self.fields["tasa_impuesto"].required = False
        if not self.instance.pk or not self.instance.tasa_impuesto:
            self.fields["tasa_impuesto"].initial = 19


class LogoUploadForm(forms.Form):
    logo = forms.ImageField(
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"})
    )


class ConfiguracionEmpresaForm(forms.ModelForm):
    """Formulario para configuración de empresa completa"""

    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            "nombre_publico",
            "tagline",
            "logo",
            "rubro_principal",
            "direccion",
            "telefono",
            "email_contacto",
            "moneda",
            "tasa_impuesto",
            "sales_tax_rate",
            "aplicar_impuesto_por_defecto",
            "dividir_por_tecnico",
            "brand_color",
            "usa_vehiculos",
            "usa_servicios",
            "usa_otros_servicios",
            "usa_kilometraje",
        ]
        widgets = {
            "nombre_publico": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre de su empresa"}
            ),
            "tagline": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Su eslogan aquí (opcional)",
                }
            ),
            "logo": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "rubro_principal": forms.Select(attrs={"class": "form-select"}),
            "direccion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Dirección completa de su empresa",
                }
            ),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+56 9 1234 5678"}
            ),
            "email_contacto": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "contacto@suempresa.com"}
            ),
            "moneda": forms.Select(attrs={"class": "form-select"}),
            "tasa_impuesto": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "sales_tax_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                    "placeholder": "0 (USA: ej. 7)",
                }
            ),
            "aplicar_impuesto_por_defecto": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "dividir_por_tecnico": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "brand_color": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
            "usa_vehiculos": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "usa_servicios": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "usa_otros_servicios": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "usa_kilometraje": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que los campos con valores por defecto no sean requeridos
        self.fields["moneda"].required = False
        self.fields["tasa_impuesto"].required = False
        self.fields["sales_tax_rate"].required = False
        self.fields["aplicar_impuesto_por_defecto"].required = False
        self.fields["dividir_por_tecnico"].required = False
        self.fields["brand_color"].required = False
        self.fields["usa_vehiculos"].required = False
        self.fields["usa_servicios"].required = False
        self.fields["usa_otros_servicios"].required = False
        self.fields["usa_kilometraje"].required = False


class ConfiguracionRubroForm(forms.ModelForm):
    """Formulario para seleccionar múltiples tipos de talleres."""

    class Meta:
        model = ConfiguracionEmpresa
        fields = ["rubros"]

    def __init__(self, *args, **kwargs):
        # Extraer request si está disponible
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        from taller.config.rubros import RUBROS_TALLER
        from taller.config.rubros_translations import get_rubros_choices_for_country

        # Detectar país del usuario/empresa
        country_code = "CL"  # Por defecto Chile

        if request:
            # 1. Intentar obtener desde empresa del usuario
            try:
                from taller.utils.empresa import get_or_create_empresa

                empresa = get_or_create_empresa(request)
                if empresa and hasattr(empresa, "pais") and empresa.pais:
                    country_code = str(empresa.pais).upper().strip()
            except Exception:
                pass

            # 2. Si no hay empresa, intentar desde request.company_country (middleware)
            if country_code == "CL" and hasattr(request, "company_country"):
                country_code = (
                    str(request.company_country).upper().strip()
                    if request.company_country
                    else "CL"
                )

            # 3. Si no hay, detectar desde la URL
            if country_code == "CL" and hasattr(request, "path"):
                path = request.path.lower()
                if path.startswith("/us/"):
                    country_code = "US"
                elif path.startswith("/mx/"):
                    country_code = "MX"
                elif path.startswith("/pe/"):
                    country_code = "PE"
                elif path.startswith("/ve/"):
                    country_code = "VE"
                elif path.startswith("/br/"):
                    country_code = "BR"
                elif path.startswith("/co/"):
                    country_code = "CO"

        # Normalizar código de país
        country_code = str(country_code).upper().strip()
        if country_code not in ["US", "CL", "MX", "PE", "VE", "BR", "CO"]:
            country_code = "CL"  # Fallback a Chile

        # Convertir JSONField a lista para el MultipleChoiceField
        if self.instance and self.instance.pk:
            rubros_actuales = self.instance.rubros or []
        else:
            rubros_actuales = []

        # Obtener traducciones por país
        translated_choices = get_rubros_choices_for_country(country_code)

        # Determinar idioma para el label
        is_spanish = country_code in {"CL", "MX", "PE", "VE", "CO"}
        is_portuguese = country_code == "BR"

        if is_portuguese:
            label_text = "Selecione os tipos de oficinas que sua empresa oferece"
        elif is_spanish:
            label_text = "Selecciona los tipos de talleres que ofrece tu empresa"
        else:
            label_text = "Select the types of workshops your company offers"

        # Configurar el campo rubros como MultipleChoiceField
        self.fields["rubros"] = forms.MultipleChoiceField(
            choices=translated_choices,
            widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            label=label_text,
            required=False,
            initial=rubros_actuales,
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Guardar como lista JSON
        instance.rubros = self.cleaned_data.get("rubros", [])
        if commit:
            instance.save()
        return instance


class ConfiguracionServiciosForm(forms.ModelForm):
    """Formulario para configurar los rubros que ofrece el taller."""

    class Meta:
        model = ConfiguracionEmpresa
        fields = ["rubros"]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        from taller.config.rubros_translations import get_rubros_choices_for_country

        # Detectar país del usuario/empresa
        country_code = "CL"  # Por defecto Chile

        if request:
            # 1. Intentar obtener desde empresa del usuario
            try:
                from taller.utils.empresa import get_or_create_empresa

                empresa = get_or_create_empresa(request)
                if empresa and hasattr(empresa, "pais") and empresa.pais:
                    country_code = str(empresa.pais).upper().strip()
            except Exception:
                pass

            # 2. Si no hay empresa, intentar desde request.company_country (middleware)
            if country_code == "CL" and hasattr(request, "company_country"):
                country_code = (
                    str(request.company_country).upper().strip()
                    if request.company_country
                    else "CL"
                )

            # 3. Si no hay, detectar desde la URL
            if country_code == "CL" and hasattr(request, "path"):
                path = request.path.lower()
                if path.startswith("/us/"):
                    country_code = "US"
                elif path.startswith("/mx/"):
                    country_code = "MX"
                elif path.startswith("/pe/"):
                    country_code = "PE"
                elif path.startswith("/ve/"):
                    country_code = "VE"
                elif path.startswith("/br/"):
                    country_code = "BR"
                elif path.startswith("/co/"):
                    country_code = "CO"

        # Normalizar código de país
        country_code = str(country_code).upper().strip()
        if country_code not in ["US", "CL", "MX", "PE", "VE", "BR", "CO"]:
            country_code = "CL"  # Fallback a Chile

        # Convertir JSONField a lista para el MultipleChoiceField
        if self.instance and self.instance.pk:
            rubros_actuales = self.instance.rubros or []
        else:
            rubros_actuales = []

        # Obtener traducciones por país
        translated_choices = get_rubros_choices_for_country(country_code)

        # Determinar idioma para el label
        is_spanish = country_code in {"CL", "MX", "PE", "VE", "CO"}
        is_portuguese = country_code == "BR"

        if is_portuguese:
            label_text = "Selecione os setores que sua oficina oferece"
        elif is_spanish:
            label_text = "Selecciona los rubros que ofrece tu taller"
        else:
            label_text = "Select the industries your shop offers"

        self.fields["rubros"] = forms.MultipleChoiceField(
            choices=translated_choices,
            widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            label=label_text,
            required=False,
            initial=rubros_actuales,
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Guardar como lista JSON
        instance.rubros = self.cleaned_data.get("rubros", [])
        if commit:
            instance.save()
        return instance
