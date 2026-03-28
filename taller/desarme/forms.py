from django import forms
from django.utils.translation import gettext_lazy as _

from taller.models.extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo
from taller.models.pieza_desarme import PiezaDesarme
from taller.models.vehiculos import Vehiculo
from taller.models.vendedor_desarme import VendedorDesarme

ANIOS_CHOICES = [("", "---------")] + [
    (y, str(y)) for y in range(2026, 1969, -1)
]  # 2026-1970 descendente

ESTADO_DESARME_CHOICES = [
    ("", _("---------")),
    ("en_yarda", _("En yarda")),
    ("en_proceso", _("In process")),
    ("completado", _("Completed")),
    ("vendido", _("Sold")),
    ("baja", _("Disposed")),
]

CARROCERIA_CHOICES = [
    ("", "---------"),
    ("sedan", "Sedán"),
    ("suv", "SUV"),
    ("pickup", "Pickup"),
    ("hatchback", "Hatchback"),
    ("coupe", "Coupé"),
    ("station_wagon", "Station Wagon"),
    ("van", "Van"),
    ("minivan", "Minivan"),
    ("convertible", "Convertible"),
    ("crossover", "Crossover"),
    ("compacto", "Compacto"),
    ("utilitario", "Utilitario"),
    ("camion", "Camión"),
    ("otro", "Otro"),
]


class VehiculoDesarmeForm(forms.ModelForm):
    """Formulario para alta/edición de vehículos de desarme. tipo_uso=DESARME, sin cliente."""

    anio = forms.TypedChoiceField(
        choices=ANIOS_CHOICES,
        coerce=lambda x: int(x) if x and str(x).strip() else None,
        label="Año",
        required=False,
        empty_value=None,
    )
    anio_otro = forms.IntegerField(
        required=False,
        label="Otro año",
        min_value=1900,
        max_value=2100,
        help_text="Año que no está en la lista (ej: 1965, 2030)",
    )
    transporte_grua = forms.DecimalField(
        required=False,
        label="Transporte/Grúa",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        initial=None,
        widget=forms.NumberInput(
            attrs={"class": "input-desarme", "step": "0.01", "placeholder": "0"}
        ),
    )
    otros_gastos = forms.DecimalField(
        required=False,
        label="Otros gastos",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        initial=None,
        widget=forms.NumberInput(
            attrs={"class": "input-desarme", "step": "0.01", "placeholder": "0"}
        ),
    )
    tipo_carroceria_otro = forms.CharField(
        required=False,
        label="Carrocería (otro)",
        max_length=80,
        widget=forms.TextInput(
            attrs={"class": "input-desarme", "placeholder": "Ej: Limousine, Off-road"}
        ),
    )

    class Meta:
        model = Vehiculo
        fields = [
            "patente",
            "vin",
            "marca",
            "modelo",
            "anio",
            "motor",
            "caja",
            "color",
            "tipo_carroceria",
            "costo_adquisicion",
            "fecha_ingreso_desarme",
            "estado_desarme",
            "ubicacion_fisica",
            "observaciones_desarme",
            "vendedor_desarme",
        ]

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        # Fijar tipo_uso, cliente y empresa ANTES de validación (el modelo exige cliente si tipo_uso=CLIENTE)
        self.instance.tipo_uso = Vehiculo.TIPO_USO_DESARME
        self.instance.cliente = None
        if self.empresa:
            self.instance.empresa = self.empresa

        self._validate_unique = True  # Validar unicidad VIN/patente por empresa

        if "vin" in self.fields:
            self.fields["vin"].required = False
        if "patente" in self.fields:
            self.fields["patente"].required = False  # Modelo acepta VIN o patente; clean() valida

        # País para filtrar motor, caja, color
        pais = "US"
        if self.empresa and hasattr(self.empresa, "pais") and self.empresa.pais:
            pais = str(self.empresa.pais).upper()[:2] or "US"

        # Motor: Select nativo (evitar dal-select2 que a veces no renderiza)
        if "motor" in self.fields:
            self.fields["motor"].widget = forms.Select(attrs={"class": "input-desarme"})
            self.fields["motor"].queryset = MotorVehiculo.objects.filter(country=pais).order_by(
                "nombre"
            )

        # Caja: Select nativo
        if "caja" in self.fields:
            self.fields["caja"].widget = forms.Select(attrs={"class": "input-desarme"})
            self.fields["caja"].queryset = CajaVehiculo.objects.filter(country=pais).order_by(
                "nombre"
            )

        # Color: Select nativo
        if "color" in self.fields:
            self.fields["color"].widget = forms.Select(attrs={"class": "input-desarme"})
            try:
                ColorVehiculo.ensure_defaults_for_country(pais)
            except Exception:
                pass
            self.fields["color"].queryset = ColorVehiculo.get_colores_para_pais(pais)

        # Carrocería: CharField con Select para permitir opciones + valor custom vía JS
        if "tipo_carroceria" in self.fields:
            choices = list(CARROCERIA_CHOICES)
            if self.instance and self.instance.pk and self.instance.tipo_carroceria:
                val = (self.instance.tipo_carroceria or "").strip()
                if val and not any(c[0] == val for c in choices if c[0]):
                    choices.append((val, val))
            self.fields["tipo_carroceria"] = forms.CharField(
                required=False,
                max_length=80,
                label="Carrocería",
                widget=forms.Select(attrs={"class": "input-desarme"}, choices=choices),
            )
            if self.instance and self.instance.pk and self.instance.tipo_carroceria:
                self.fields["tipo_carroceria"].initial = self.instance.tipo_carroceria
        # Vendedor: select por empresa
        if "vendedor_desarme" in self.fields:
            self.fields["vendedor_desarme"].widget = forms.Select(attrs={"class": "input-desarme"})
            if self.empresa:
                self.fields["vendedor_desarme"].queryset = VendedorDesarme.objects.filter(
                    empresa=self.empresa
                ).order_by("nombre")
            self.fields["vendedor_desarme"].required = False
        # Motor, caja, color no requeridos
        for f in ("motor", "caja", "color", "tipo_carroceria"):
            if f in self.fields:
                self.fields[f].required = False
        # Calendario desplegable para fecha
        if "fecha_ingreso_desarme" in self.fields:
            self.fields["fecha_ingreso_desarme"].widget = forms.DateInput(
                attrs={"type": "date", "class": "input-desarme"}
            )
        # Lista de opciones para estado
        if "estado_desarme" in self.fields:
            choices = list(ESTADO_DESARME_CHOICES)
            if self.instance and self.instance.pk and self.instance.estado_desarme:
                val = self.instance.estado_desarme
                if val and not any(c[0] == val for c in choices if c[0]):
                    choices.insert(1, (val, val))
            self.fields["estado_desarme"] = forms.ChoiceField(
                choices=choices,
                required=False,
                label="Estado desarme",
                widget=forms.Select(attrs={"class": "input-desarme"}),
            )
            if self.instance and self.instance.pk and self.instance.estado_desarme:
                self.fields["estado_desarme"].initial = self.instance.estado_desarme
        # Observaciones más compacto (textarea reducido)
        if "observaciones_desarme" in self.fields:
            self.fields["observaciones_desarme"].widget.attrs.update(
                {"rows": 2, "class": "input-desarme"}
            )
        # Estilo input-desarme en todos los campos
        for field in self.fields.values():
            if hasattr(field.widget, "attrs") and "input-desarme" not in (
                field.widget.attrs.get("class") or ""
            ):
                cls = (field.widget.attrs.get("class") or "").strip()
                field.widget.attrs["class"] = f"{cls} input-desarme".strip()
        for f in (
            "costo_adquisicion",
            "fecha_ingreso_desarme",
            "estado_desarme",
            "ubicacion_fisica",
            "observaciones_desarme",
            "transporte_grua",
            "otros_gastos",
            "tipo_carroceria_otro",
            "vendedor_desarme",
        ):
            if f in self.fields:
                self.fields[f].required = False

    def clean(self):
        from django.core.exceptions import ValidationError

        data = super().clean()
        anio = data.get("anio")
        anio_otro = data.get("anio_otro")
        if anio_otro:
            data["anio"] = anio_otro
        elif not anio:
            raise ValidationError({"anio": "Seleccione un año o ingrese uno personalizado."})

        # Validar unicidad VIN y patente por empresa (evitar IntegrityError en save)
        if self.empresa:
            vin = (data.get("vin") or "").strip()
            patente = (data.get("patente") or "").strip()
            if vin:
                qs = Vehiculo.objects.filter(empresa=self.empresa, vin=vin)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    self.add_error("vin", "Ya existe un vehículo con este VIN en esta empresa.")
            if patente:
                qs = Vehiculo.objects.filter(empresa=self.empresa, patente=patente)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    self.add_error(
                        "patente", "Ya existe un vehículo con esta patente en esta empresa."
                    )

        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo_uso = Vehiculo.TIPO_USO_DESARME
        instance.cliente = None
        if self.empresa:
            instance.empresa = self.empresa
        # Carrocería: si eligió "otro" y hay texto, guardar ese texto
        tc = (self.cleaned_data.get("tipo_carroceria") or "").strip()
        tc_otro = (self.cleaned_data.get("tipo_carroceria_otro") or "").strip()
        if tc == "otro" and tc_otro:
            instance.tipo_carroceria = tc_otro
        elif tc:
            instance.tipo_carroceria = tc
        # Añadir transporte/grua y otros gastos a observaciones (vendedor_desarme ya es FK)
        extras = []
        t = self.cleaned_data.get("transporte_grua")
        if t is not None and t > 0:
            extras.append(f"Transporte/Grúa: {t}")
        o = self.cleaned_data.get("otros_gastos")
        if o is not None and o > 0:
            extras.append(f"Otros gastos: {o}")
        if extras and instance.observaciones_desarme:
            instance.observaciones_desarme = (
                instance.observaciones_desarme.rstrip() + "\n" + "\n".join(extras)
            )
        elif extras:
            instance.observaciones_desarme = "\n".join(extras)
        if commit:
            instance.save()
        return instance


class PiezaDesarmeForm(forms.ModelForm):
    """Formulario para alta/edición de piezas de desarme."""

    class Meta:
        model = PiezaDesarme
        # Subconjunto seguro que debería existir también en producción
        fields = [
            "vehiculo",
            "codigo",
            "nombre",
            "cantidad",
            "estado_pieza",
            "ubicacion_fisica",
            "observaciones",
        ]

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
        # Observaciones: textarea compacto (pocas líneas)
        if "observaciones" in self.fields:
            self.fields["observaciones"].widget = forms.Textarea(
                attrs={"rows": 3, "class": "input-desarme pieza-obs", "placeholder": ""}
            )
