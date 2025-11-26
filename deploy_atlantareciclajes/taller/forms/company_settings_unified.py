# -*- coding: utf-8 -*-
"""
Formulario unificado para ConfiguracionEmpresa con Address

Convenciones:
- Usa modelo Address para legal_address
- Campos virtuales country/state/city para UI
- clean() crea Address automáticamente
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.ubicacion import Ciudad, Estado
from ubicacion.models import Address


class CompanySettingsForm(forms.ModelForm):
    """
    Formulario unificado de configuración de empresa con soporte para Address.

    Campos virtuales para UI:
    - country: Select de país
    - state: Código de estado
    - city: FK a Ciudad
    - legal_line1, legal_line2, legal_postal_code: Campos de dirección legal

    El método clean() crea automáticamente el Address.
    """

    # === CAMPOS VIRTUALES PARA DIRECCIÓN LEGAL ===

    legal_country = forms.ChoiceField(
        choices=(
            ("CL", "Chile"),
            ("US", "USA"),
            ("MX", "México"),
            ("BR", "Brasil"),
            ("PE", "Perú"),
            ("VE", "Venezuela"),
        ),
        required=False,
        label=_("País"),
        widget=forms.Select(attrs={"id": "id_legal_country", "class": "form-control"}),
    )

    legal_state = forms.CharField(
        required=False,
        label=_("Estado/Departamento"),
        widget=forms.TextInput(attrs={"id": "id_legal_state", "class": "form-control"}),
    )

    legal_city = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        required=False,
        label=_("Ciudad"),
        widget=forms.Select(attrs={"id": "id_legal_city", "class": "form-control"}),
    )

    legal_line1 = forms.CharField(
        required=False,
        label=_("Dirección Línea 1"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Calle, número, edificio")}
        ),
    )

    legal_line2 = forms.CharField(
        required=False,
        label=_("Dirección Línea 2"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Oficina, piso, departamento (opcional)"),
            }
        ),
    )

    legal_postal_code = forms.CharField(
        required=False,
        label=_("Código Postal"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Zipcode / CEP / Código Postal")}
        ),
    )

    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            "nombre_publico",
            "tagline",
            "logo",
            "telefono",
            "email_contacto",
            "sitio_web",
            "moneda",
            "tasa_impuesto",
            "aplicar_impuesto_por_defecto",
            "brand_color",
            # legal_address se setea en clean()
        ]
        widgets = {
            "nombre_publico": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Nombre público de la empresa")}
            ),
            "tagline": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Eslogan o frase descriptiva")}
            ),
            "logo": forms.FileInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("+56 9 1234 5678")}
            ),
            "email_contacto": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": _("contacto@empresa.com")}
            ),
            "sitio_web": forms.URLInput(
                attrs={"class": "form-control", "placeholder": _("https://empresa.com")}
            ),
            "moneda": forms.Select(attrs={"class": "form-control"}),
            "tasa_impuesto": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "100"}
            ),
            "aplicar_impuesto_por_defecto": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "brand_color": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si la empresa ya tiene legal_address, prellenar campos virtuales
        addr = getattr(self.instance, "legal_address", None)
        if addr and addr.city:
            st = addr.city.estado

            # Prellenar país
            self.fields["legal_country"].initial = st.pais

            # Prellenar estado (código)
            self.fields["legal_state"].initial = getattr(st, "codigo", "") or getattr(
                st, "code", ""
            )

            # Prellenar ciudad (queryset filtrado)
            self.fields["legal_city"].queryset = Ciudad.objects.filter(estado=st).order_by("nombre")
            self.fields["legal_city"].initial = addr.city_id

            # Prellenar campos de dirección
            self.fields["legal_line1"].initial = addr.line1
            self.fields["legal_line2"].initial = addr.line2
            self.fields["legal_postal_code"].initial = addr.postal_code

        # Auto-detectar país desde empresa
        elif self.instance.empresa and hasattr(self.instance.empresa, "pais"):
            pais = self.instance.empresa.pais
            self.fields["legal_country"].initial = pais

    def clean(self):
        """
        Validación y creación automática de legal_address.

        Si se proporcionan legal_country, legal_city y legal_line1,
        crea un Address y lo asigna a legal_address.
        """
        cd = super().clean()

        country = (cd.get("legal_country") or "").upper()
        state_code = (cd.get("legal_state") or "").upper()
        city = cd.get("legal_city")
        line1 = self.data.get("legal_line1", "").strip()

        # Si hay datos de dirección completos, crear/actualizar Address
        if country and city and line1:
            try:
                # Verificar consistencia: ciudad debe pertenecer al país
                if city.estado.pais != country:
                    raise forms.ValidationError(
                        {"legal_city": _("La ciudad seleccionada no pertenece al país.")}
                    )

                # Actualizar dirección existente o crear nueva
                if self.instance.legal_address:
                    # Actualizar
                    addr = self.instance.legal_address
                    addr.line1 = line1
                    addr.line2 = self.data.get("legal_line2", "").strip()
                    addr.city = city
                    addr.postal_code = self.data.get("legal_postal_code", "").strip()

                    # Actualizar coordenadas si se proporcionan
                    lat = self.data.get("legal_latitude", "").strip()
                    lng = self.data.get("legal_longitude", "").strip()
                    if lat:
                        addr.latitude = lat
                    if lng:
                        addr.longitude = lng

                    addr.save()
                else:
                    # Crear nueva
                    addr = Address.objects.create(
                        line1=line1,
                        line2=self.data.get("legal_line2", "").strip(),
                        city=city,
                        postal_code=self.data.get("legal_postal_code", "").strip(),
                        company=self.instance.empresa,  # Asociar a empresa
                    )

                # Asignar a configuración
                cd["legal_address"] = addr

            except Ciudad.DoesNotExist:
                raise forms.ValidationError({"legal_city": _("Ciudad no encontrada.")})
            except Exception as e:
                raise forms.ValidationError(
                    {"legal_city": _("Error al crear dirección: %(error)s") % {"error": str(e)}}
                )

        return cd

    def save(self, commit=True):
        """Guardar configuración con legal_address"""
        instance = super().save(commit=False)

        if commit:
            instance.save()

        return instance
