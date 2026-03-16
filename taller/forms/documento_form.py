# Formulario unificado y mejorado para Documento
from dal import autocomplete

from django import forms

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo


# Helper centralizado para namespaces de autocompletado
def _ns(country: str) -> str:
    return "usa_autocomplete" if (country or "").upper() == "US" else "cl_autocomplete"


class DocumentoForm(forms.ModelForm):
    """
    Formulario avanzado para Documento con:
    - Autocompletado DAL multi-país
    - Labels dinámicos según país
    - Filtrado multi-tenant
    - Validaciones robustas
    - IDs únicos para JavaScript
    """

    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),  # Se ajustará en __init__
        widget=autocomplete.ModelSelect2(
            url="",  # Se establecerá dinámicamente
            attrs={
                "data-placeholder": "🔍 Buscar cliente...",
                "data-minimum-input-length": 2,
            },
        ),
        required=True,
    )

    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.none(),  # Se ajustará en __init__
        widget=autocomplete.ModelSelect2(
            url="",  # Se establecerá dinámicamente
            forward=["cliente"],
            attrs={
                "data-placeholder": "🔍 Buscar vehículo...",
                "data-minimum-input-length": 1,
            },
        ),
        required=False,
    )

    # Campos JSON para filas dinámicas
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
        help_text="Kilometraje del vehículo al momento de crear el documento",
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
            "kilometraje",  # Mantenido para compatibilidad, pero no se usará
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
        ]
        # NOTA: kilometraje_ingreso NO está en fields porque no es un campo del modelo

        # Campos obligatorios: solo los esenciales
        # NOTA: 'numero' se autogenera en el modelo, NO es requerido en el form
        required_fields = ["tipo", "fecha_emision", "cliente"]

    def __init__(self, *args, **kwargs):
        # Extraer argumentos personalizados
        self.user = kwargs.pop("user", None)
        self.empresa = kwargs.pop("empresa", None)
        self.country = kwargs.pop("country", "CL")

        # Si no se pasó empresa, intentar obtenerla del usuario
        if not self.empresa and self.user:
            try:
                self.empresa = getattr(self.user, "empresa", None)
            except Exception:
                pass

        super().__init__(*args, **kwargs)

        # Configurar URLs de autocompletado dinámicamente
        self.fields["cliente"].widget.url = f"{_ns(self.country)}:cliente"
        self.fields["vehiculo"].widget.url = f"{_ns(self.country)}:vehiculo"

        # Configurar querysets filtrados por empresa (vehículo solo tipo CLIENTE para documentos)
        if self.empresa:
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=self.empresa)
            self.fields["vehiculo"].queryset = Vehiculo.objects.filter(
                empresa=self.empresa, tipo_uso=Vehiculo.TIPO_USO_CLIENTE
            )
            self.fields["tecnico_responsable"].queryset = self.empresa.tecnicos.all()

        # Configurar labels según el país
        self._configure_labels_by_country()

        # Configurar choices dinámicos
        self._configure_dynamic_choices()

        # Configurar widgets con IDs únicos para JavaScript
        self._configure_widget_ids()

        # Configurar campos requeridos: solo los esenciales
        self._configure_required_fields()

        # Configurar campo kilometraje_ingreso dinámicamente
        self._configure_kilometraje_ingreso()

    def _configure_labels_by_country(self):
        """Configura labels dinámicos según el país y rubro de la empresa"""
        # Obtener configuración de la empresa para determinar rubro
        responsable_label = "Técnico Responsable"  # Default
        if self.empresa:
            try:
                config = getattr(self.empresa, "config", None)
                if config:
                    responsable_label = config.get_responsable_label(self.country)
            except Exception:
                pass  # Si no hay config, usar default

        if self.country == "US":
            labels = {
                "tipo": "Document Type",
                "cliente": "Customer",
                "vehiculo": "Vehicle",
                "tecnico_responsable": (
                    responsable_label
                    if responsable_label != "Técnico Responsable"
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
                "vehiculo": "Vehículo",
                "tecnico_responsable": responsable_label,
                "kilometraje": "Kilometraje",
                "kilometraje_ingreso": "Kilometraje Actual",
                "millas": "Millas",
                "observaciones": "Observaciones",
                "pagado": "Pagado",
                "metodo_pago": "Método de Pago",
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
        """Configura choices dinámicos según el país"""
        if self.country == "US":
            self.fields["tipo"].choices = [
                ("OT", "Work Order"),
                ("PRES", "Estimate"),  # Estimate
                ("FAC", "Invoice/Receipt"),  # Invoice
            ]
            self.fields["payment_status"].choices = [
                ("pending", "Pending"),
                ("paid", "Paid"),
                ("partial", "Partial"),
                ("canceled", "Canceled"),
            ]
            # Millas solo en USA
            if "millas" in self.fields:
                self.fields["millas"].required = False
                self.fields["kilometraje"].required = False
        else:  # CL (Chile)
            self.fields["tipo"].choices = [
                ("OT", "Orden de Trabajo"),
                ("PRES", "Presupuesto"),
                ("FAC", "Factura/Boleta"),  # Factura/Boleta
            ]
            self.fields["payment_status"].choices = [
                ("pending", "Pendiente"),
                ("paid", "Pagado"),
                ("partial", "Parcial"),
                ("canceled", "Anulado"),
            ]
            # Kilometraje en Chile, millas no aplica
            if "millas" in self.fields:
                self.fields["millas"].widget = forms.HiddenInput()
                self.fields["millas"].required = False

    def _configure_widget_ids(self):
        """Configura IDs únicos para todos los campos (para JavaScript)"""
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
        """Configura qué campos son requeridos: solo los esenciales"""
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

        # El campo número es opcional: si está vacío se autogenera
        if "numero" in self.fields:
            self.fields["numero"].required = False
            self.fields["numero"].help_text = "Se generará automáticamente si se deja vacío"

    def _configure_kilometraje_ingreso(self):
        """
        Configura el campo kilometraje_ingreso según el país y si hay vehículo.
        Si hay un vehículo en la instancia, muestra el kilometraje actual como sugerencia.
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

        # Si hay una instancia con vehículo, mostrar el kilometraje actual como placeholder
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
        # Ya se configuró en _configure_labels_by_country

    def clean(self):
        """Validaciones robustas multi-tenant"""
        cleaned_data = super().clean()

        # Validar que cliente pertenece a la empresa
        cliente = cleaned_data.get("cliente")
        vehiculo = cleaned_data.get("vehiculo")

        if cliente and self.empresa and cliente.empresa != self.empresa:
            raise forms.ValidationError("El cliente seleccionado no pertenece a tu empresa.")

        if vehiculo and self.empresa and vehiculo.empresa != self.empresa:
            raise forms.ValidationError("El vehículo seleccionado no pertenece a tu empresa.")

        # Validar que vehículo pertenece al cliente (solo si el vehículo tiene cliente; tipo CLIENTE siempre lo tiene)
        if (
            vehiculo
            and cliente
            and getattr(vehiculo, "cliente_id", None) is not None
            and vehiculo.cliente_id != cliente.id
        ):
            raise forms.ValidationError("El vehículo seleccionado no pertenece al cliente.")

        # Validaciones específicas por país
        if self.country == "CL":
            # En Chile, millas no debe tener valor
            if cleaned_data.get("millas"):
                raise forms.ValidationError(
                    "El campo millas no puede usarse en documentos de Chile."
                )
            # En Chile, si hay vehículo, el kilometraje_ingreso debería ser requerido
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
                        "Debe especificar al menos kilometraje o millas cuando hay un vehículo."
                    )

        return cleaned_data

    def save(self, commit=True):
        """
        Override save para:
        1. Guardar el documento
        2. Procesar datos JSON y crear líneas del documento
        3. Crear el registro de kilometraje si se proporcionó kilometraje_ingreso
        """
        # Extraer kilometraje_ingreso antes de guardar (no es campo del modelo)
        # Lo guardamos en una variable de instancia para usarlo después
        kilometraje_ingreso = self.cleaned_data.get("kilometraje_ingreso")

        # Guardar el documento (kilometraje_ingreso no está en fields del Meta,
        # así que Django lo ignorará automáticamente)
        documento = super().save(commit=commit)

        if commit:
            # Procesar datos JSON solo si el documento se guardó
            self._process_json_data(documento)

            # Crear registro de kilometraje si se proporcionó y hay vehículo
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
            return  # No crear registro si no es válido

        # Obtener técnico responsable (puede ser None)
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
        """Procesa los datos JSON y crea las líneas del documento"""
        import json

        from taller.models.lineas_documento import (
            LineaRepuesto,
            ORIGEN_DESARME,
            ORIGEN_STOCK_BODEGA,
        )

        repuestos_data = self.cleaned_data.get("repuestos_json", "[]")
        if repuestos_data:
            try:
                repuestos = json.loads(repuestos_data)
                for rep_data in repuestos:
                    if not (rep_data.get("codigo") or rep_data.get("nombre")):
                        continue
                    origen = rep_data.get("origen_repuesto") or ORIGEN_STOCK_BODEGA
                    is_desarme = origen == ORIGEN_DESARME and rep_data.get("pieza_desarme_id")
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
                    else:
                        kwargs["pieza_desarme_id"] = None
                        rep_id = rep_data.get("id")
                        if rep_id not in (None, ""):
                            kwargs["repuesto_id"] = int(rep_id)
                    LineaRepuesto.objects.create(**kwargs)
            except (json.JSONDecodeError, ValueError):
                pass

        # Procesar servicios (SIN cantidad: forzamos cantidad=1)
        servicios_data = self.cleaned_data.get("servicios_json", "[]")
        if servicios_data:
            try:
                servicios = json.loads(servicios_data)
                for serv_data in servicios:
                    if serv_data.get("servicio_id"):
                        from taller.models.lineas_documento import LineaServicio

                        LineaServicio.objects.create(
                            documento=documento,
                            servicio_id=serv_data.get("servicio_id"),
                            cantidad=1,  # forzamos 1 (sin cantidad en UI)
                            precio_unitario=serv_data.get("precio", 0),
                        )
            except (json.JSONDecodeError, ValueError):
                pass  # Ignorar datos JSON inválidos

        # Procesar otros servicios
        otros_data = self.cleaned_data.get("otros_json", "[]")
        if otros_data:
            try:
                otros = json.loads(otros_data)
                for otro_data in otros:
                    if otro_data.get("servicio_id"):
                        from taller.models.lineas_documento import LineaOtroServicio

                        LineaOtroServicio.objects.create(
                            documento=documento,
                            servicio_id=otro_data.get("servicio_id"),
                            empresa_externa=otro_data.get("empresa_ext", ""),
                            cantidad=otro_data.get("cantidad", 1),
                            precio_taller=otro_data.get("precio_taller", 0),
                            precio_cliente=otro_data.get("precio", 0),
                        )
            except (json.JSONDecodeError, ValueError):
                pass  # Ignorar datos JSON inválidos
