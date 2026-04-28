import json
from decimal import Decimal, InvalidOperation

# Formulario unificado y mejorado para Documento
from dal import autocomplete

from django import forms
from django.db import transaction
from django.utils.translation import get_language

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo


# Helper centralizado para namespaces de autocompletado
def _ns(country: str) -> str:
    return "usa_autocomplete" if (country or "").upper() == "US" else "cl_autocomplete"


def _normalize_numeric_string(value):
    if value in (None, "", "None"):
        return ""
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace(" ", "")
    comma = text.rfind(",")
    dot = text.rfind(".")
    if comma > -1 and dot > -1:
        if comma > dot:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma > -1:
        text = text.replace(".", "").replace(",", ".")
    else:
        if text.count(".") > 1:
            last = text.rfind(".")
            text = text[:last].replace(".", "") + "." + text[last + 1 :]
        else:
            text = text.replace(",", "")
    return text


def _to_decimal(value, default=Decimal("0")):
    normalized = _normalize_numeric_string(value)
    if not normalized:
        return default
    try:
        return Decimal(normalized)
    except (InvalidOperation, TypeError, ValueError):
        return default


def _to_positive_int(value, default=1):
    try:
        return max(1, int(_to_decimal(value, Decimal(default))))
    except (TypeError, ValueError):
        return default


def _to_optional_int(value):
    if value in (None, "", "None"):
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_json_list_field(value):
    if value in (None, "", "None", "null"):
        return []

    parsed = value
    if isinstance(value, str):
        parsed = json.loads(value)

    if parsed is None:
        return []
    if not isinstance(parsed, list):
        raise ValueError("Expected a JSON list")

    normalized = []
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("Each line item must be an object")
        normalized.append(item)
    return normalized


class DocumentoForm(forms.ModelForm):
    """
    Formulario avanzado para Documento con:
    - Autocompletado DAL multi-paÃ­s
    - Labels dinÃ¡micos segÃºn paÃ­s
    - Filtrado multi-tenant
    - Validaciones robustas
    - IDs Ãºnicos para JavaScript
    """

    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),  # Se ajustarÃ¡ en __init__
        widget=autocomplete.ModelSelect2(
            url="",  # Se establecerÃ¡ dinÃ¡micamente
            attrs={
                "data-placeholder": "ðŸ” Buscar cliente...",
                "data-minimum-input-length": 2,
            },
        ),
        required=True,
    )

    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.none(),  # Se ajustarÃ¡ en __init__
        widget=autocomplete.ModelSelect2(
            url="",  # Se establecerÃ¡ dinÃ¡micamente
            forward=["cliente"],
            attrs={
                "data-placeholder": "ðŸ” Buscar vehÃ­culo...",
                "data-minimum-input-length": 1,
            },
        ),
        required=False,
    )

    # Campos JSON para filas dinÃ¡micas
    repuestos_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    servicios_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    otros_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    payment_status = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "form-control form-select w-full text-base"}),
        choices=[
            ("pending", "Pendiente"),
            ("paid", "Pagado"),
            ("partial", "Parcial"),
            ("canceled", "Anulado"),
        ],
    )
    apply_vat = forms.BooleanField(required=False)

    # Campo de kilometraje que NO se guarda en el modelo Documento
    # Se usa solo para crear el KilometrajeRegistro asociado
    kilometraje_ingreso = forms.IntegerField(
        label="Kilometraje Actual",
        required=False,
        min_value=0,
        help_text="Kilometraje del vehÃ­culo al momento de crear el documento",
    )

    class Meta:
        model = Documento
        fields = [
            "tipo",
            "numero",
            "fecha_emision",
            "cliente",
            "vehiculo",
            "tecnico_responsable",
            "kilometraje",  # Mantenido para compatibilidad, pero no se usarÃ¡
            "millas",
            "observaciones",
            "pagado",
            "payment_status",
            "metodo_pago",
            "ult4",
            "monto_pagado",
            "saldo_pendiente",
            "fecha_pago",
            "nota_pago",
            "descuento",
            "apply_vat",
        ]
        # NOTA: kilometraje_ingreso NO estÃ¡ en fields porque no es un campo del modelo

        # Campos obligatorios: solo los esenciales
        # NOTA: 'numero' se autogenera en el modelo, NO es requerido en el form
        required_fields = ["tipo", "fecha_emision", "cliente"]

    def __init__(self, *args, **kwargs):
        # Extraer argumentos personalizados
        self.user = kwargs.pop("user", None)
        self.empresa = kwargs.pop("empresa", None)
        self.country = kwargs.pop("country", "CL")
        # Idioma para labels/choices: define textos visibles (es/en/pt)
        # Si no se pasa, usa get_language() o fallback por paÃ­s (retrocompat)
        lang = kwargs.pop("language", None)
        self.language = (lang or get_language() or "").split("-")[0] or (
            "en" if (self.country or "").upper() == "US" else "es"
        )

        # Si no se pasÃ³ empresa, intentar obtenerla del usuario
        if not self.empresa and self.user:
            try:
                self.empresa = getattr(self.user, "empresa", None)
            except Exception:
                pass

        super().__init__(*args, **kwargs)

        # Configurar URLs de autocompletado dinÃ¡micamente
        self.fields["cliente"].widget.url = f"{_ns(self.country)}:cliente"
        self.fields["vehiculo"].widget.url = f"{_ns(self.country)}:vehiculo"

        # Configurar querysets filtrados por empresa (vehÃ­culo solo tipo CLIENTE para documentos)
        if self.empresa:
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=self.empresa)
            self.fields["vehiculo"].queryset = Vehiculo.objects.filter(
                empresa=self.empresa, tipo_uso=Vehiculo.TIPO_USO_CLIENTE
            )
            self.fields["tecnico_responsable"].queryset = self.empresa.tecnicos.all()

        # Configurar labels segÃºn idioma (no paÃ­s)
        self._configure_labels_by_language()

        # Configurar choices dinÃ¡micos (labels por idioma; visibilidad millas por paÃ­s)
        self._configure_dynamic_choices()

        # Configurar widgets con IDs Ãºnicos para JavaScript
        self._configure_widget_ids()

        # Configurar campos requeridos: solo los esenciales
        self._configure_required_fields()

        # Configurar campo kilometraje_ingreso dinÃ¡micamente
        self._configure_kilometraje_ingreso()

    def _configure_labels_by_language(self):
        """Configura labels dinÃ¡micos segÃºn idioma (no paÃ­s). PaÃ­s solo para rubro tÃ©cnico."""
        # Obtener configuraciÃ³n de la empresa para determinar rubro
        responsable_label = "TÃ©cnico Responsable"  # Default
        if self.empresa:
            try:
                config = getattr(self.empresa, "config", None)
                if config:
                    responsable_label = config.get_responsable_label(self.country)
            except Exception:
                pass  # Si no hay config, usar default

        if self.language == "en":
            labels = {
                "tipo": "Document Type",
                "cliente": "Customer",
                "vehiculo": "Vehicle",
                "tecnico_responsable": (
                    responsable_label
                    if responsable_label != "TÃ©cnico Responsable"
                    else "Assigned Technician"
                ),
                "kilometraje": "Mileage",
                "kilometraje_ingreso": "Current Mileage",
                "millas": "Miles",
                "observaciones": "Notes",
                "pagado": "Paid",
                "metodo_pago": "Payment Method",
                "monto_pagado": "Amount Paid",
                "saldo_pendiente": "Outstanding Balance",
                "fecha_pago": "Payment Date",
                "nota_pago": "Payment Notes",
                "descuento": "Discount",
                "payment_status": "Payment Status",
            }
        else:  # CL (Chile)
            labels = {
                "tipo": "Tipo de Documento",
                "cliente": "Cliente",
                "vehiculo": "VehÃ­culo",
                "tecnico_responsable": responsable_label,
                "kilometraje": "Kilometraje",
                "kilometraje_ingreso": "Kilometraje Actual",
                "millas": "Millas",
                "observaciones": "Observaciones",
                "pagado": "Pagado",
                "metodo_pago": "MÃ©todo de Pago",
                "monto_pagado": "Monto Pagado",
                "saldo_pendiente": "Saldo Pendiente",
                "fecha_pago": "Fecha de Pago",
                "nota_pago": "Nota de Pago",
                "descuento": "Descuento",
                "payment_status": "Estado de Pago",
            }

        for field_name, label in labels.items():
            if field_name in self.fields:
                self.fields[field_name].label = label

    def _configure_dynamic_choices(self):
        """Configura choices dinÃ¡micos: labels por idioma; visibilidad millas por paÃ­s."""
        # Labels de choices segÃºn idioma
        if self.language == "en":
            self.fields["tipo"].choices = [
                ("OT", "Work Order"),
                ("PRES", "Estimate"),
                ("FAC", "Invoice/Receipt"),
            ]
            self.fields["payment_status"].choices = [
                ("pending", "Pending"),
                ("paid", "Paid"),
                ("partial", "Partial"),
                ("canceled", "Canceled"),
            ]
        else:
            self.fields["tipo"].choices = [
                ("OT", "Orden de Trabajo"),
                ("PRES", "Presupuesto"),
                ("FAC", "Factura/Boleta"),
            ]
            self.fields["payment_status"].choices = [
                ("pending", "Pendiente"),
                ("paid", "Pagado"),
                ("partial", "Parcial"),
                ("canceled", "Anulado"),
            ]
        # Visibilidad de millas por paÃ­s (US muestra millas; CL/otros la ocultan)
        if "millas" in self.fields:
            if (self.country or "").upper() == "US":
                self.fields["millas"].required = False
                self.fields["kilometraje"].required = False
            else:
                self.fields["millas"].widget = forms.HiddenInput()
                self.fields["millas"].required = False

    def _configure_widget_ids(self):
        """Configura IDs Ãºnicos para todos los campos (para JavaScript)"""
        widget_ids = {
            "tipo": "id_tipo",
            "numero": "id_numero",
            "fecha_emision": "id_fecha_emision",
            "cliente": "id_cliente",
            "vehiculo": "id_vehiculo",
            "tecnico_responsable": "id_tecnico_responsable",
            "kilometraje": "id_kilometraje",
            "kilometraje_ingreso": "id_kilometraje_ingreso",
            "millas": "id_millas",
            "observaciones": "id_observaciones",
            "pagado": "id_pagado",
            "metodo_pago": "id_metodo_pago",
            "ult4": "id_ult4",
            "monto_pagado": "id_monto_pagado",
            "saldo_pendiente": "id_saldo_pendiente",
            "fecha_pago": "id_fecha_pago",
            "nota_pago": "id_nota_pago",
            "descuento": "id_descuento",
            "payment_status": "id_payment_status",
        }

        for field_name, widget_id in widget_ids.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.setdefault("id", widget_id)

    def _configure_required_fields(self):
        """Configura quÃ© campos son requeridos: solo los esenciales"""
        # Campos obligatorios: solo los esenciales
        # NOTA: 'numero' se autogenera en el modelo, NO es requerido en el form
        required_fields = ["tipo", "fecha_emision", "cliente"]

        # Marcar todos los campos como no requeridos por defecto
        for field_name in self.fields:
            self.fields[field_name].required = False

        # Marcar solo los campos esenciales como requeridos
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True

        # El campo nÃºmero es opcional: si estÃ¡ vacÃ­o se autogenera
        if "numero" in self.fields:
            self.fields["numero"].required = False
            self.fields["numero"].help_text = "Se generarÃ¡ automÃ¡ticamente si se deja vacÃ­o"

    def _configure_kilometraje_ingreso(self):
        """
        Configura el campo kilometraje_ingreso segÃºn el paÃ­s y si hay vehÃ­culo.
        Si hay un vehÃ­culo en la instancia, muestra el kilometraje actual como sugerencia.
        """
        if "kilometraje_ingreso" not in self.fields:
            return

        # Configurar widget con atributos
        self.fields["kilometraje_ingreso"].widget.attrs.update(
            {
                "class": "form-control",
                "min": "0",
                "step": "1",
            }
        )

        # Si hay una instancia con vehÃ­culo, mostrar el kilometraje actual como placeholder
        if self.instance and self.instance.pk and self.instance.vehiculo:
            try:
                kilometraje_actual = self.instance.vehiculo.kilometraje_actual
                if kilometraje_actual:
                    self.fields["kilometraje_ingreso"].widget.attrs[
                        "placeholder"
                    ] = f"Kilometraje actual: {kilometraje_actual} km"
            except Exception:
                pass

        # En USA, el label puede ser "Mileage" o "Current Mileage"
        # Ya se configurÃ³ en _configure_labels_by_language

    def clean(self):
        """Validaciones robustas multi-tenant"""
        cleaned_data = super().clean()
        self._parsed_line_items = {}

        # Validar que cliente pertenece a la empresa
        cliente = cleaned_data.get("cliente")
        vehiculo = cleaned_data.get("vehiculo")

        if cliente and self.empresa and cliente.empresa != self.empresa:
            raise forms.ValidationError("El cliente seleccionado no pertenece a tu empresa.")

        if vehiculo and self.empresa and vehiculo.empresa != self.empresa:
            raise forms.ValidationError("El vehÃ­culo seleccionado no pertenece a tu empresa.")

        # Validar que vehÃ­culo pertenece al cliente (solo si el vehÃ­culo tiene cliente; tipo CLIENTE siempre lo tiene)
        if (
            vehiculo
            and cliente
            and getattr(vehiculo, "cliente_id", None) is not None
            and vehiculo.cliente_id != cliente.id
        ):
            raise forms.ValidationError("El vehÃ­culo seleccionado no pertenece al cliente.")

        # Validaciones especÃ­ficas por paÃ­s
        if self.country == "CL":
            # En Chile, millas no debe tener valor
            if cleaned_data.get("millas"):
                raise forms.ValidationError(
                    "El campo millas no puede usarse en documentos de Chile."
                )
            # En Chile, si hay vehÃ­culo, el kilometraje_ingreso deberÃ­a ser requerido
            vehiculo = cleaned_data.get("vehiculo")
            if vehiculo and not cleaned_data.get("kilometraje_ingreso"):
                # Advertencia, no error - permitir crear sin kilometraje si es necesario
                pass
        elif self.country == "US":
            # En USA, si existe el campo millas usarlo como alternativa;
            # si no existe en el formulario renderizado, validar solo kilometraje_ingreso.
            vehiculo = cleaned_data.get("vehiculo")
            if vehiculo:
                kilometraje = cleaned_data.get("kilometraje_ingreso")
                millas = cleaned_data.get("millas") if "millas" in self.fields else None
                if not kilometraje and not millas:
                    raise forms.ValidationError(
                        "Debe especificar al menos kilometraje o millas cuando hay un vehÃ­culo."
                    )

        for field_name in ("repuestos_json", "servicios_json", "otros_json"):
            try:
                self._parsed_line_items[field_name] = _parse_json_list_field(
                    cleaned_data.get(field_name, "[]")
                )
            except (TypeError, ValueError, json.JSONDecodeError):
                self.add_error(field_name, "Formato invalido de lineas del documento.")

        return cleaned_data

    def save(self, commit=True):
        """
        Override save para:
        1. Guardar el documento
        2. Procesar datos JSON y crear lÃ­neas del documento
        3. Crear el registro de kilometraje si se proporcionÃ³ kilometraje_ingreso
        """
        # Extraer kilometraje_ingreso antes de guardar (no es campo del modelo)
        # Lo guardamos en una variable de instancia para usarlo despuÃ©s
        kilometraje_ingreso = self.cleaned_data.get("kilometraje_ingreso")

        # Guardar el documento (kilometraje_ingreso no estÃ¡ en fields del Meta,
        # asÃ­ que Django lo ignorarÃ¡ automÃ¡ticamente)
        documento = super().save(commit=False)
        if self.empresa:
            documento.empresa = self.empresa

        if not commit:
            return documento

        with transaction.atomic():
            documento.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
            # Procesar datos JSON solo si el documento se guardÃ³
            self._process_json_data(documento)

            # Recalcular totales del documento tras crear las lÃ­neas
            documento.recompute_totals(persist=True)

            # Crear registro de kilometraje si se proporcionÃ³ y hay vehÃ­culo
            if kilometraje_ingreso is not None and documento.vehiculo:
                self._crear_registro_kilometraje(documento, kilometraje_ingreso)

        return documento

    def _crear_registro_kilometraje(self, documento, kilometraje):
        """
        Crea un registro de kilometraje asociado al documento.

        Args:
            documento: Instancia de Documento guardada
            kilometraje: Valor del kilometraje a registrar
        """
        from taller.models import KilometrajeRegistro

        # Validar que el kilometraje sea un entero positivo
        try:
            kilometraje_int = int(kilometraje)
            if kilometraje_int < 0:
                return  # No crear registro si es negativo
        except (ValueError, TypeError):
            return  # No crear registro si no es vÃ¡lido

        # Obtener tÃ©cnico responsable (puede ser None)
        tecnico = documento.tecnico_responsable

        # Crear el registro de kilometraje
        KilometrajeRegistro.objects.create(
            empresa=documento.empresa,
            vehiculo=documento.vehiculo,
            documento=documento,
            kilometraje=kilometraje_int,
            registrado_por=tecnico,
        )

    def _process_json_data(self, documento):
        """Procesa los datos JSON y recrea las lineas del documento."""
        from taller.models.catalogo_servicios import Service
        from taller.models.lineas_documento import (
            LineaOtroServicio,
            LineaRepuesto,
            LineaServicio,
            ORIGEN_DESARME,
            ORIGEN_EXTERNO,
            ORIGEN_STOCK_BODEGA,
        )
        from taller.servicios.models import Servicio

        parsed_line_items = getattr(self, "_parsed_line_items", {})
        repuestos = parsed_line_items.get("repuestos_json", [])
        servicios = parsed_line_items.get("servicios_json", [])
        otros = parsed_line_items.get("otros_json", [])

        # Reemplazar todas las lineas evita arrastre de estado al editar.
        documento.lineas_repuesto.all().delete()
        documento.lineas_servicio.all().delete()
        documento.lineas_otro_servicio.all().delete()

        allowed_origins = {ORIGEN_EXTERNO, ORIGEN_STOCK_BODEGA, ORIGEN_DESARME}

        for rep_data in repuestos:
            codigo = (rep_data.get("codigo") or "").strip()
            nombre = (rep_data.get("nombre") or "").strip()
            repuesto_id = _to_optional_int(rep_data.get("repuesto_id") or rep_data.get("id"))
            part_id = _to_optional_int(rep_data.get("part_id"))
            pieza_desarme_id = _to_optional_int(rep_data.get("pieza_desarme_id"))

            if not (codigo or nombre or repuesto_id or part_id or pieza_desarme_id):
                continue

            origen = rep_data.get("origen_repuesto")
            if pieza_desarme_id:
                origen = ORIGEN_DESARME
            elif repuesto_id is not None or part_id is not None:
                origen = origen or ORIGEN_STOCK_BODEGA
            else:
                origen = ORIGEN_EXTERNO
            if origen not in allowed_origins:
                origen = (
                    ORIGEN_EXTERNO
                    if repuesto_id is None and part_id is None
                    else ORIGEN_STOCK_BODEGA
                )

            kwargs = {
                "documento": documento,
                "codigo": codigo or nombre or str(repuesto_id or part_id or ""),
                "nombre": nombre or codigo or "Repuesto",
                "cantidad": _to_positive_int(rep_data.get("cantidad"), default=1),
                "precio_unitario": _to_decimal(
                    rep_data.get("precio", rep_data.get("precio_unitario", 0))
                ),
                "descuento": _to_decimal(rep_data.get("descuento", 0)),
                "origen_repuesto": origen,
                "tecnico_responsable_id": _to_optional_int(rep_data.get("tecnico_responsable_id")),
            }

            if origen == ORIGEN_DESARME and pieza_desarme_id:
                kwargs["pieza_desarme_id"] = pieza_desarme_id
                kwargs["costo_linea"] = _to_decimal(rep_data.get("costo_linea", 0))
            else:
                # BLOQUEADO: flujo inseguro eliminado
                if part_id is not None:
                    kwargs["part_id"] = part_id
                costo_linea = rep_data.get("costo_linea")
                if costo_linea not in (None, "", "None"):
                    kwargs["costo_linea"] = _to_decimal(costo_linea)

            LineaRepuesto.objects.create(**kwargs)

        for serv_data in servicios:
            servicio_id = _to_optional_int(serv_data.get("servicio_id"))
            service_id = _to_optional_int(serv_data.get("service_id"))
            nombre = (serv_data.get("nombre") or "").strip()

            if not (servicio_id or service_id or nombre):
                continue

            if not nombre and servicio_id:
                nombre = (
                    Servicio.objects.filter(pk=servicio_id).values_list("nombre", flat=True).first()
                    or ""
                )
            if not nombre and service_id:
                nombre = (
                    Service.objects.filter(pk=service_id).values_list("code", flat=True).first()
                    or ""
                )
            if not nombre:
                continue

            LineaServicio.objects.create(
                documento=documento,
                servicio_id=servicio_id,
                service_id=service_id,
                nombre=nombre,
                cantidad=1,
                precio_unitario=_to_decimal(
                    serv_data.get("precio", serv_data.get("precio_unitario", 0))
                ),
                descuento=_to_decimal(serv_data.get("descuento", 0)),
                tecnico_responsable_id=_to_optional_int(serv_data.get("tecnico_responsable_id")),
            )

        for otro_data in otros:
            servicio_id = _to_optional_int(otro_data.get("servicio_id"))
            nombre = (otro_data.get("nombre") or "").strip()

            if not (servicio_id or nombre):
                continue

            if not nombre and servicio_id:
                nombre = (
                    Servicio.objects.filter(pk=servicio_id).values_list("nombre", flat=True).first()
                    or ""
                )
            if not nombre:
                continue

            LineaOtroServicio.objects.create(
                documento=documento,
                servicio_id=servicio_id,
                nombre=nombre,
                empresa_externa=(otro_data.get("empresa_ext") or "").strip(),
                cantidad=_to_positive_int(otro_data.get("cantidad"), default=1),
                costo_interno=_to_decimal(
                    otro_data.get("precio_taller", otro_data.get("costo_interno", 0))
                ),
                precio_cliente=_to_decimal(
                    otro_data.get("precio", otro_data.get("precio_cliente", 0))
                ),
                tecnico_responsable_id=_to_optional_int(otro_data.get("tecnico_responsable_id")),
            )

    def _process_json_data_legacy(self, documento):
        """Procesa los datos JSON y crea las lÃ­neas del documento"""
        import json

        from taller.models.lineas_documento import (
            LineaRepuesto,
            ORIGEN_DESARME,
            ORIGEN_EXTERNO,
            ORIGEN_STOCK_BODEGA,
        )

        repuestos_data = self.cleaned_data.get("repuestos_json", "[]")
        if repuestos_data:
            try:
                repuestos = json.loads(repuestos_data)
                for rep_data in repuestos:
                    if not (rep_data.get("codigo") or rep_data.get("nombre")):
                        continue
                    rep_id = rep_data.get("id")
                    pieza_desarme_id = rep_data.get("pieza_desarme_id")
                    if pieza_desarme_id:
                        origen = ORIGEN_DESARME
                    elif rep_id not in (None, ""):
                        origen = rep_data.get("origen_repuesto") or ORIGEN_STOCK_BODEGA
                    else:
                        origen = ORIGEN_EXTERNO
                    is_desarme = origen == ORIGEN_DESARME and pieza_desarme_id
                    kwargs = {
                        "documento": documento,
                        "codigo": rep_data.get("codigo", ""),
                        "nombre": rep_data.get("nombre", ""),
                        "cantidad": rep_data.get("cantidad", 1),
                        "precio_unitario": rep_data.get("precio", 0),
                        "descuento": rep_data.get("descuento", 0),
                        "origen_repuesto": origen,
                    }
                    if is_desarme:
                        pd_id = rep_data.get("pieza_desarme_id")
                        kwargs["pieza_desarme_id"] = int(pd_id) if pd_id else None
                        kwargs["repuesto_id"] = None
                        kwargs["part_id"] = None
                        costo = rep_data.get("costo_linea")
                        if costo is not None:
                            kwargs["costo_linea"] = costo
                    elif origen == ORIGEN_EXTERNO:
                        kwargs["pieza_desarme_id"] = None
                        kwargs["repuesto_id"] = None
                        kwargs["part_id"] = None
                    else:
                        kwargs["pieza_desarme_id"] = None
                        if rep_id not in (None, ""):
                            from taller.models import Repuesto

                            repuesto = Repuesto.objects.filter(
                                id=int(rep_id), empresa=documento.empresa
                            ).first()

                            if not repuesto:
                                raise Exception("SECURITY: intento de acceso cross-tenant")

                            kwargs["repuesto_id"] = repuesto.id
                    LineaRepuesto.objects.create(**kwargs)
            except (json.JSONDecodeError, ValueError):
                pass

        # Procesar servicios (SIN cantidad: forzamos cantidad=1)
        servicios_data = self.cleaned_data.get("servicios_json", "[]")
        if servicios_data:
            try:
                servicios = json.loads(servicios_data)
                for serv_data in servicios:
                    servicio_id = serv_data.get("servicio_id")
                    nombre = serv_data.get("nombre", "")
                    if servicio_id or nombre:
                        from taller.models.lineas_documento import LineaServicio

                        kwargs = {
                            "documento": documento,
                            "nombre": nombre,
                            "cantidad": 1,  # forzamos 1 (sin cantidad en UI)
                            "precio_unitario": serv_data.get("precio", 0),
                        }
                        if servicio_id not in (None, ""):
                            kwargs["servicio_id"] = servicio_id
                        LineaServicio.objects.create(**kwargs)
            except (json.JSONDecodeError, ValueError):
                pass  # Ignorar datos JSON invÃ¡lidos

        # Procesar otros servicios
        otros_data = self.cleaned_data.get("otros_json", "[]")
        if otros_data:
            try:
                otros = json.loads(otros_data)
                for otro_data in otros:
                    servicio_id = otro_data.get("servicio_id")
                    nombre = otro_data.get("nombre", "")
                    if servicio_id or nombre:
                        from taller.models.lineas_documento import LineaOtroServicio

                        kwargs = {
                            "documento": documento,
                            "nombre": nombre,
                            "empresa_externa": otro_data.get("empresa_ext", ""),
                            "cantidad": otro_data.get("cantidad", 1),
                            "costo_interno": otro_data.get("precio_taller", 0),
                            "precio_cliente": otro_data.get("precio", 0),
                        }
                        if servicio_id not in (None, ""):
                            kwargs["servicio_id"] = servicio_id
                        LineaOtroServicio.objects.create(**kwargs)
            except (json.JSONDecodeError, ValueError):
                pass  # Ignorar datos JSON invÃ¡lidos
