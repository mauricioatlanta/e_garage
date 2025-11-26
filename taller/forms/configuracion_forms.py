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
        self.fields["aplicar_impuesto_por_defecto"].required = False
        self.fields["dividir_por_tecnico"].required = False
        self.fields["brand_color"].required = False
        self.fields["usa_vehiculos"].required = False
        self.fields["usa_servicios"].required = False
        self.fields["usa_otros_servicios"].required = False
        self.fields["usa_kilometraje"].required = False


class ConfiguracionRubroForm(forms.ModelForm):
    """Formulario compacto para rubro y módulos del documento."""

    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            "rubro_principal",
            "usa_vehiculos",
            "usa_servicios",
            "usa_otros_servicios",
            "usa_kilometraje",
        ]
        widgets = {
            "rubro_principal": forms.Select(attrs={"class": "form-select"}),
            "usa_vehiculos": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "usa_servicios": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "usa_otros_servicios": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "usa_kilometraje": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    # Traducciones de rubros
    RUBRO_TRANSLATIONS = {
        "en": {
            "WORKSHOP": "Full-service auto shop",
            "WORKSHOP_MOTO": "Motorcycle shop",
            "WORKSHOP_HEAVY": "Truck/bus shop",
            "EXHAUST": "Exhaust and mufflers",
            "PARTS": "Auto parts store",
            "TIRE": "Tire shop / Vulcanization",
            "BODYSHOP": "Body shop / Paint",
            "DETAILING": "Car wash, detailing and aesthetics",
            "ELECTRIC": "Automotive electrical / electronics",
            "GLASS_AUDIO": "Windshields, glass and audio / accessories",
            "FLEET": "Fleet maintenance",
            "MIXED": "Mixed (multiple industries)",
        },
        "es": {
            "WORKSHOP": "Taller mecánico integral",
            "WORKSHOP_MOTO": "Taller de motos",
            "WORKSHOP_HEAVY": "Taller de camiones/buses",
            "EXHAUST": "Escapes y mufflers",
            "PARTS": "Casa de repuestos / Autopartes",
            "TIRE": "Vulcanización / Neumáticos y llantas",
            "BODYSHOP": "Carrocería / Pintura",
            "DETAILING": "Lavado, detailing y estética",
            "ELECTRIC": "Electricidad / electrónica automotriz",
            "GLASS_AUDIO": "Parabrisas, vidrios y audio / accesorios",
            "FLEET": "Mantención de flotas empresariales",
            "MIXED": "Mixto (varios rubros)",
        },
    }

    def __init__(self, *args, **kwargs):
        # Extraer request si está disponible
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # Determinar idioma
        lang_code = "es"  # Por defecto español
        if request:
            # Intentar obtener idioma del request (verificar múltiples atributos)
            lang_code = (
                getattr(request, "LANGUAGE_CODE", None)
                or getattr(request, "preferred_language", None)
                or getattr(request, "language", None)
            )
            
            # Si no está disponible, intentar detectar desde la URL
            if not lang_code and hasattr(request, "path"):
                path = request.path
                if "/us/" in path or "/en/" in path:
                    lang_code = "en"
                elif "/es/" in path:
                    lang_code = "es"
                else:
                    # Intentar obtener del país de la empresa si está disponible
                    try:
                        from taller.utils.empresa import get_or_create_empresa
                        empresa = get_or_create_empresa(request)
                        if empresa and hasattr(empresa, "pais"):
                            is_spanish = empresa.pais in {"CL", "MX", "PE", "VE", "BR"}
                            lang_code = "es" if is_spanish else "en"
                    except Exception:
                        pass  # Si falla, usar el valor por defecto

        # Normalizar lang_code (solo usar los primeros 2 caracteres)
        if lang_code:
            lang_code = lang_code[:2].lower()
        else:
            lang_code = "es"

        # Traducir label del campo rubro_principal
        if lang_code == "en":
            self.fields["rubro_principal"].label = "Primary Industry"
        else:
            self.fields["rubro_principal"].label = "Rubro Principal"

        # Traducir opciones del campo rubro_principal
        translations = self.RUBRO_TRANSLATIONS.get(lang_code, self.RUBRO_TRANSLATIONS["es"])
        original_choices = ConfiguracionEmpresa.RUBRO_CHOICES
        translated_choices = [
            (value, translations.get(value, label)) for value, label in original_choices
        ]
        self.fields["rubro_principal"].choices = translated_choices
