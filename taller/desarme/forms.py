from decimal import Decimal, InvalidOperation

from django import forms
from django.utils.translation import gettext_lazy as _

from taller.models.extras_vehiculo import (
    CajaVehiculo,
    CajaVehiculoEmpresa,
    ColorVehiculo,
    MotorVehiculo,
    MotorVehiculoEmpresa,
)
from taller.models.pieza_desarme import CONDICION_CHOICES, PiezaDesarme
from taller.models.vehiculo_desarme import ESTADO_DESARME_CHOICES as _MODELO_ESTADO_DESARME_CHOICES
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo
from taller.models.vendedor_desarme import VendedorDesarme

ANIOS_CHOICES = [("", "---------")] + [
    (y, str(y)) for y in range(2026, 1969, -1)
]  # 2026-1970 descendente

# Fuente única de verdad: los choices del modelo VehiculoDesarme (no una lista
# propia del form). ESTADO_DESARME_CHOICES vive como constante a nivel de módulo
# en taller/models/vehiculo_desarme.py, no como atributo de clase.
ESTADO_DESARME_CHOICES = [("", _("---------"))] + list(_MODELO_ESTADO_DESARME_CHOICES)

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
    ("moto", "Motocicleta"),
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
    marca_otro = forms.CharField(
        required=False,
        label="Marca (otro)",
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "input-desarme", "placeholder": "Ej: BYD, Great Wall, Chery"}
        ),
    )
    modelo_otro = forms.CharField(
        required=False,
        label="Modelo (otro)",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "input-desarme", "placeholder": "Ej: Tiggo 3, Jolion"}
        ),
    )

    class Meta:
        model = VehiculoDesarme
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
            "precio_compra",
            "fecha_ingreso_desarme",
            "estado_desarme",
            "ubicacion_fisica",
            "observaciones_desarme",
            "vendedor_desarme",
        ]

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        # VehiculoDesarme no tiene cliente ni tipo_uso -- a diferencia de Vehiculo,
        # no hace falta forzarlos acá; el modelo ya es "solo desarme" por diseño.
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
        # Guardado para uso en clean_motor/clean_caja (debe ser el mismo país usado aquí
        # para poblar los <select>, si no los IDs no calzan).
        self._pais = pais

        # Ajustar campos monetarios según país
        _PAISES_ENTERO = {"CL", "AR", "UY", "PE", "VE", "CO"}
        _is_integer = pais in _PAISES_ENTERO
        self._is_money_integer = _is_integer
        _decs = 0 if _is_integer else 2
        for _fname in ("precio_compra", "transporte_grua", "otros_gastos"):
            if _fname not in self.fields:
                continue
            if _is_integer:
                _f = self.fields[_fname]
                # Parchar to_python para limpiar separadores de miles CLP ("120.000" → "120000")
                # ANTES de que DecimalField ejecute sus validadores. Sin esto, Django falla
                # en field.clean() antes de que llegue a clean_<fieldname>().
                _orig_tp = _f.to_python
                def _cl_to_python(v, _o=_orig_tp):
                    if isinstance(v, str):
                        v = v.replace(".", "").replace(",", "").strip()
                    return _o(v)
                _f.to_python = _cl_to_python
                # Actualizar decimal_places y el DecimalValidator al nuevo valor
                _f.decimal_places = 0
                from django.core.validators import DecimalValidator as _DV
                _f.validators = [v for v in _f.validators if not isinstance(v, _DV)]
                if getattr(_f, "max_digits", None):
                    _f.validators.append(_DV(_f.max_digits, 0))
                _f.widget = forms.TextInput(
                    attrs={
                        "class": "input-desarme",
                        "inputmode": "numeric",
                        "placeholder": "0",
                        "data-money-cl": "1",
                    }
                )
                # Mostrar valor inicial con separador de miles: 20000 → "20.000"
                if _fname in self.initial and self.initial[_fname] is not None:
                    try:
                        from decimal import Decimal as _D
                        self.initial[_fname] = f"{int(_D(str(self.initial[_fname]))):,}".replace(",", ".")
                    except Exception:
                        pass
            else:
                self.fields[_fname].decimal_places = _decs
                self.fields[_fname].widget = forms.NumberInput(
                    attrs={"class": "input-desarme", "step": "0.01", "placeholder": "0.00"}
                )

        # Motor: CharField (no ModelChoiceField) para poder aceptar "empresa:<id>"
        # (motor privado creado vía AJAX) además del id del catálogo global. La
        # resolución real ocurre en clean_motor(); acá solo se arma el <select>.
        if "motor" in self.fields:
            motor_label = self.fields["motor"].label
            motor_choices = [("", "---------")] + [
                (str(m.pk), m.nombre)
                for m in MotorVehiculo.objects.filter(country=pais).order_by("nombre")
            ]
            motor_initial = None
            if self.instance and self.instance.pk:
                if getattr(self.instance, "motor_empresa_id", None):
                    motor_initial = f"empresa:{self.instance.motor_empresa_id}"
                    motor_choices.append((motor_initial, str(self.instance.motor_empresa)))
                elif self.instance.motor_id:
                    motor_initial = str(self.instance.motor_id)
            self.fields["motor"] = forms.CharField(
                required=False,
                label=motor_label,
                initial=motor_initial,
                widget=forms.Select(choices=motor_choices, attrs={"class": "input-desarme"}),
            )

        # Caja: mismo patrón que motor.
        if "caja" in self.fields:
            caja_label = self.fields["caja"].label
            caja_choices = [("", "---------")] + [
                (str(c.pk), c.nombre)
                for c in CajaVehiculo.objects.filter(country=pais).order_by("nombre")
            ]
            caja_initial = None
            if self.instance and self.instance.pk:
                if getattr(self.instance, "caja_empresa_id", None):
                    caja_initial = f"empresa:{self.instance.caja_empresa_id}"
                    caja_choices.append((caja_initial, str(self.instance.caja_empresa)))
                elif self.instance.caja_id:
                    caja_initial = str(self.instance.caja_id)
            self.fields["caja"] = forms.CharField(
                required=False,
                label=caja_label,
                initial=caja_initial,
                widget=forms.Select(choices=caja_choices, attrs={"class": "input-desarme"}),
            )

        # Color: Select nativo
        if "color" in self.fields:
            self.fields["color"].widget = forms.Select(attrs={"class": "input-desarme"})
            try:
                ColorVehiculo.ensure_defaults_for_country(pais)
            except Exception:
                pass
            self.fields["color"].queryset = ColorVehiculo.get_colores_para_pais(pais)
            _col_clean = self.fields["color"].clean
            def _lenient_color(val, _orig=_col_clean):
                try:
                    return _orig(val)
                except Exception:
                    return None
            self.fields["color"].clean = _lenient_color

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
            "precio_compra",
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

    def _post_clean(self):
        # Para países con catálogo FK (no USA), limpiar marca_texto/modelo_texto del
        # instance ANTES de que ModelForm llame a instance.full_clean(). Sin esto,
        # el model.clean() rechaza vehículos creados con campos de texto libre (ej: seed demo).
        # Excepción: si el usuario eligió "Otro", se conserva el texto libre.
        _pais = str(getattr(self.empresa, "pais", "US") or "US").upper()[:2]
        if _pais not in {"US"} and self.instance:
            if not self.cleaned_data.get("marca_otro"):
                self.instance.marca_texto = ""
            if not self.cleaned_data.get("modelo_otro"):
                self.instance.modelo_texto = ""
        super()._post_clean()

    def _clean_money_cl(self, field_name):
        """Limpia separadores de miles CLP antes de validar (ej: '20.000' → Decimal(20000))."""
        raw = self.data.get(self.add_prefix(field_name) or field_name, "").strip()
        raw = raw.replace(".", "").replace(",", "") if raw else raw
        return self.fields[field_name].clean(raw)

    def clean_precio_compra(self):
        if getattr(self, "_is_money_integer", False):
            return self._clean_money_cl("precio_compra")
        return self.cleaned_data.get("precio_compra")

    def clean_transporte_grua(self):
        if getattr(self, "_is_money_integer", False):
            return self._clean_money_cl("transporte_grua")
        return self.cleaned_data.get("transporte_grua")

    def clean_otros_gastos(self):
        if getattr(self, "_is_money_integer", False):
            return self._clean_money_cl("otros_gastos")
        return self.cleaned_data.get("otros_gastos")

    def clean_motor(self):
        """Aceptar motor global (id numérico) o privado de empresa ("empresa:<id>").

        Portado de VehiculoForm.clean_motor (taller/vehiculos/forms.py). A diferencia
        del wrapper "lenient" anterior, acá una referencia inválida es un error de
        validación explícito, no se traga en silencio.
        """
        raw_value = (self.cleaned_data.get("motor") or "").strip()
        empresa = self.empresa
        pais = self._pais
        modelo = self.cleaned_data.get("modelo")

        if not raw_value:
            self._motor_empresa_obj = None
            return None

        if raw_value.startswith("empresa:"):
            if not empresa or not modelo:
                raise forms.ValidationError(
                    "Motor privado no válido: falta empresa o modelo."
                )
            private_id = raw_value.split(":", 1)[1]
            try:
                motor_privado = MotorVehiculoEmpresa.objects.get(
                    pk=private_id,
                    empresa=empresa,
                    modelo=modelo,
                    country=pais,
                )
            except (MotorVehiculoEmpresa.DoesNotExist, ValueError):
                raise forms.ValidationError("Motor privado no válido.")
            self._motor_empresa_obj = motor_privado
            return None

        try:
            motor = MotorVehiculo.objects.get(pk=raw_value, country=pais)
        except (MotorVehiculo.DoesNotExist, ValueError):
            raise forms.ValidationError("Motor no válido.")
        self._motor_empresa_obj = None
        return motor

    def clean_caja(self):
        """Aceptar caja global (id numérico) o privada de empresa ("empresa:<id>").

        Portado de VehiculoForm.clean_caja (taller/vehiculos/forms.py). Fail loud:
        una referencia inválida levanta ValidationError, no se traga en silencio.
        """
        raw_value = (self.cleaned_data.get("caja") or "").strip()
        empresa = self.empresa
        pais = self._pais
        modelo = self.cleaned_data.get("modelo")

        if not raw_value:
            self._caja_empresa_obj = None
            return None

        if raw_value.startswith("empresa:"):
            if not empresa or not modelo:
                raise forms.ValidationError(
                    "Caja privada no válida: falta empresa o modelo."
                )
            private_id = raw_value.split(":", 1)[1]
            try:
                caja_privada = CajaVehiculoEmpresa.objects.get(
                    pk=private_id,
                    empresa=empresa,
                    modelo=modelo,
                    country=pais,
                )
            except (CajaVehiculoEmpresa.DoesNotExist, ValueError):
                raise forms.ValidationError("Caja privada no válida.")
            self._caja_empresa_obj = caja_privada
            return None

        try:
            caja = CajaVehiculo.objects.get(pk=raw_value, country=pais)
        except (CajaVehiculo.DoesNotExist, ValueError):
            raise forms.ValidationError("Caja no válida.")
        self._caja_empresa_obj = None
        return caja

    def clean(self):
        from django.core.exceptions import ValidationError

        data = super().clean()
        anio = data.get("anio")
        anio_otro = data.get("anio_otro")
        if anio_otro:
            data["anio"] = anio_otro
        elif not anio:
            raise ValidationError({"anio": "Seleccione un año o ingrese uno personalizado."})

        # Marca/modelo con escape "Otro": si eligió texto libre, limpia la FK para evitar conflicto
        if data.get("marca_otro"):
            data["marca"] = None
        if data.get("modelo_otro"):
            data["modelo"] = None

        # Al menos VIN o Patente deben estar presentes (el modelo lo exige en clean() pero
        # como error non-field que el template no muestra; lo capturamos aquí con add_error).
        vin = (data.get("vin") or "").strip()
        patente = (data.get("patente") or "").strip()
        if not vin and not patente:
            self.add_error("patente", "Debe registrar al menos Patente o VIN.")
            self.add_error("vin", "Debe registrar al menos Patente o VIN.")

        # Validar unicidad VIN y patente contra Vehiculo Y VehiculoDesarme -- evita
        # IntegrityError en save y que un mismo VIN quede en un vehículo de cliente
        # (Vehiculo) y uno de desarme (VehiculoDesarme) a la vez. Se excluye el
        # Vehiculo legacy origen de este mismo VehiculoDesarme (vehiculo_origen_id),
        # si lo tiene: no es un duplicado, es su propio par migrado por 0078/0141.
        if self.empresa:
            origen_id = getattr(self.instance, "vehiculo_origen_id", None)
            if vin:
                qs_vehiculo = Vehiculo.objects.filter(empresa=self.empresa, vin=vin)
                if origen_id:
                    qs_vehiculo = qs_vehiculo.exclude(pk=origen_id)
                qs_desarme = VehiculoDesarme.objects.filter(empresa=self.empresa, vin=vin)
                if self.instance.pk:
                    qs_desarme = qs_desarme.exclude(pk=self.instance.pk)
                if qs_vehiculo.exists() or qs_desarme.exists():
                    self.add_error("vin", "Ya existe un vehículo con este VIN en esta empresa.")
            if patente:
                qs_vehiculo = Vehiculo.objects.filter(empresa=self.empresa, patente=patente)
                if origen_id:
                    qs_vehiculo = qs_vehiculo.exclude(pk=origen_id)
                qs_desarme = VehiculoDesarme.objects.filter(empresa=self.empresa, patente=patente)
                if self.instance.pk:
                    qs_desarme = qs_desarme.exclude(pk=self.instance.pk)
                if qs_vehiculo.exists() or qs_desarme.exists():
                    self.add_error(
                        "patente", "Ya existe un vehículo con esta patente en esta empresa."
                    )

        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.empresa:
            instance.empresa = self.empresa
        # Motor/caja privados de empresa: clean_motor/clean_caja ya resolvieron el
        # objeto (o None) y devolvieron None para el campo global cuando corresponde,
        # así que acá solo queda asignar la FK privada calculada.
        instance.motor_empresa = getattr(self, "_motor_empresa_obj", None)
        instance.caja_empresa = getattr(self, "_caja_empresa_obj", None)
        # Carrocería: si eligió "otro" y hay texto, guardar ese texto
        tc = (self.cleaned_data.get("tipo_carroceria") or "").strip()
        tc_otro = (self.cleaned_data.get("tipo_carroceria_otro") or "").strip()
        if tc == "otro" and tc_otro:
            instance.tipo_carroceria = tc_otro
        elif tc:
            instance.tipo_carroceria = tc
        # Marca/modelo con escape "Otro": guardar texto libre en marca_texto/modelo_texto
        marca_otro = (self.cleaned_data.get("marca_otro") or "").strip()
        if marca_otro:
            instance.marca = None
            instance.marca_texto = marca_otro
        modelo_otro = (self.cleaned_data.get("modelo_otro") or "").strip()
        if modelo_otro:
            instance.modelo = None
            instance.modelo_texto = modelo_otro
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
            "vehiculo_desarme",
            "codigo",
            "nombre",
            "cantidad",
            "condicion",
            "estado_pieza",
            "precio_venta_sugerido",
            "ubicacion_fisica",
            "observaciones",
        ]

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        self.vehiculo = kwargs.pop("vehiculo", None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields["vehiculo_desarme"].queryset = VehiculoDesarme.objects.filter(
                empresa=self.empresa,
            ).order_by("patente", "vin")
        if self.vehiculo:
            self.fields["vehiculo_desarme"].initial = self.vehiculo
            self.fields["vehiculo_desarme"].disabled = True
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
        # Condición: select nativo
        if "condicion" in self.fields:
            from taller.models.pieza_desarme import CONDICION_CHOICES
            self.fields["condicion"].widget = forms.Select(
                attrs={"class": "input-desarme"},
                choices=CONDICION_CHOICES,
            )
        # Observaciones: textarea compacto (pocas líneas)
        if "observaciones" in self.fields:
            self.fields["observaciones"].widget = forms.Textarea(
                attrs={"rows": 3, "class": "input-desarme pieza-obs", "placeholder": ""}
            )
        # Precio: para países sin decimal (CL y la mayoría de LATAM) usar TextInput
        # con formato local (punto como separador de miles) y parsear en clean().
        pais = getattr(self.empresa, "pais", "CL") if self.empresa else "CL"
        self._precio_pais = pais
        if "precio_venta_sugerido" in self.fields:
            if pais in ("US", "BR"):
                self.fields["precio_venta_sugerido"].widget = forms.NumberInput(
                    attrs={"class": "input-desarme", "min": "0", "step": "0.01"}
                )
            else:
                self.fields["precio_venta_sugerido"].widget = forms.TextInput(
                    attrs={"class": "input-desarme", "placeholder": "Ej: 12.500"}
                )
                if self.instance and self.instance.pk and self.instance.precio_venta_sugerido:
                    raw = int(self.instance.precio_venta_sugerido)
                    self.initial["precio_venta_sugerido"] = f"{raw:,}".replace(",", ".")

    def clean_precio_venta_sugerido(self):
        val = self.cleaned_data.get("precio_venta_sugerido")
        if val in (None, ""):
            return None
        if isinstance(val, str):
            # Remover separador de miles (punto en CL) y normalizar coma decimal
            val = val.replace(".", "").replace(",", ".").strip()
            if not val:
                return None
            try:
                return Decimal(val)
            except InvalidOperation:
                raise forms.ValidationError("Ingrese un valor numérico válido (ej: 12.500).")
        return val


class PiezaSueltaForm(forms.Form):
    """
    Formulario corto para registrar una pieza suelta sin vehículo completo.
    Crea un Vehiculo placeholder automáticamente al guardar.
    """

    nombre = forms.CharField(
        max_length=255,
        label="Nombre de la pieza",
        widget=forms.TextInput(attrs={"class": "input-desarme", "placeholder": "Ej: Tambor de freno trasero"}),
    )
    condicion = forms.ChoiceField(
        choices=CONDICION_CHOICES,
        label="Condición",
        widget=forms.Select(attrs={"class": "input-desarme"}),
    )
    precio_venta_sugerido = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        label="Precio de venta sugerido",
        widget=forms.NumberInput(attrs={"class": "input-desarme", "min": "0", "step": "1"}),
    )
    codigo = forms.CharField(
        required=False,
        max_length=100,
        label="Código (opcional)",
        widget=forms.TextInput(attrs={"class": "input-desarme", "placeholder": "Se auto-genera si se deja vacío"}),
    )
    cantidad = forms.IntegerField(
        required=False,
        min_value=1,
        initial=1,
        label="Cantidad",
        widget=forms.NumberInput(attrs={"class": "input-desarme", "min": "1"}),
    )
    imagen = forms.ImageField(
        required=False,
        label="Foto de la pieza (opcional)",
    )
    # Datos del vehículo de origen (solo trazabilidad, todos opcionales)
    marca_texto = forms.CharField(
        required=False,
        max_length=100,
        label="Marca del auto de origen",
        widget=forms.TextInput(attrs={"class": "input-desarme", "placeholder": "Ej: Toyota"}),
    )
    modelo_texto = forms.CharField(
        required=False,
        max_length=150,
        label="Modelo del auto de origen",
        widget=forms.TextInput(attrs={"class": "input-desarme", "placeholder": "Ej: Corolla"}),
    )
    anio_origen = forms.IntegerField(
        required=False,
        min_value=1900,
        max_value=2100,
        label="Año del auto de origen",
        widget=forms.NumberInput(attrs={"class": "input-desarme", "placeholder": "Ej: 2018"}),
    )
