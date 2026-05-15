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
    payment_status = forms.CharField(required=False)
    apply_vat = forms.BooleanField(required=False)

    class Meta:
        model = Documento
        fields = [
            "tipo",
            "numero",
            "fecha_emision",
            "cliente",
            "vehiculo",
            "tecnico_responsable",
            "kilometraje",
            "millas",
            "observaciones",
            "pagado",
            "metodo_pago",
            "ult4",
            "monto_pagado",
            "saldo_pendiente",
            "fecha_pago",
            "nota_pago",
            "descuento",
        ]

        # Campos obligatorios: solo los esenciales
        # NOTA: 'numero' se autogenera en el modelo, NO es requerido en el form
        required_fields = ["tipo", "fecha_emision", "cliente"]

    def __init__(self, *args, **kwargs):
        # Extraer argumentos personalizados
        self.user = kwargs.pop("user", None)
        self.empresa = kwargs.pop("empresa", None)
        self.country = kwargs.pop("country", "CL")

        super().__init__(*args, **kwargs)

        # Configurar URLs de autocompletado dinámicamente
        self.fields["cliente"].widget.url = f"{_ns(self.country)}:cliente"
        self.fields["vehiculo"].widget.url = f"{_ns(self.country)}:vehiculo"

        # Configurar querysets filtrados por empresa
        if self.empresa:
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=self.empresa)
            self.fields["vehiculo"].queryset = Vehiculo.objects.filter(empresa=self.empresa)
            self.fields["tecnico_responsable"].queryset = self.empresa.tecnicos.all()

        # Configurar labels según el país
        self._configure_labels_by_country()

        # Configurar choices dinámicos
        self._configure_dynamic_choices()

        # Configurar widgets con IDs únicos para JavaScript
        self._configure_widget_ids()

        # Configurar campos requeridos: solo los esenciales
        self._configure_required_fields()

    def _configure_labels_by_country(self):
        """Configura labels dinámicos según el país"""
        if self.country == "US":
            labels = {
                "tipo": "Document Type",
                "cliente": "Customer",
                "vehiculo": "Vehicle",
                "tecnico_responsable": "Assigned Technician",
                "kilometraje": "Mileage",
                "millas": "Miles",
                "observaciones": "Notes",
                "pagado": "Paid",
                "metodo_pago": "Payment Method",
                "monto_pagado": "Amount Paid",
                "saldo_pendiente": "Outstanding Balance",
                "fecha_pago": "Payment Date",
                "nota_pago": "Payment Notes",
                "descuento": "Discount",
            }
        else:  # CL (Chile)
            labels = {
                "tipo": "Tipo de Documento",
                "cliente": "Cliente",
                "vehiculo": "Vehículo",
                "tecnico_responsable": "Técnico Responsable",
                "kilometraje": "Kilometraje",
                "millas": "Millas",
                "observaciones": "Observaciones",
                "pagado": "Pagado",
                "metodo_pago": "Método de Pago",
                "monto_pagado": "Monto Pagado",
                "saldo_pendiente": "Saldo Pendiente",
                "fecha_pago": "Fecha de Pago",
                "nota_pago": "Nota de Pago",
                "descuento": "Descuento",
            }

        for field_name, label in labels.items():
            if field_name in self.fields:
                self.fields[field_name].label = label

    def _configure_dynamic_choices(self):
        """Configura choices dinámicos según el país"""
        if self.country == "US":
            self.fields["tipo"].choices = [
                ("OT", "Work Order"),
                ("PRES", "Estimate"),
                ("FAC", "Invoice/Receipt"),  # Cambiado de "REC" a "FAC"
            ]

            # Millas solo en USA
            if "millas" in self.fields:
                self.fields["millas"].required = False
                self.fields["kilometraje"].required = False
        else:  # CL (Chile)
            self.fields["tipo"].choices = [
                ("OT", "Orden de Trabajo"),
                ("PRES", "Presupuesto"),
                ("FAC", "Factura/Boleta"),  # Cambiado de "REC" a "FAC"
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

        # Validar que vehículo pertenece al cliente
        if vehiculo and cliente and vehiculo.cliente != cliente:
            raise forms.ValidationError("El vehículo seleccionado no pertenece al cliente.")

        # Validaciones específicas por país
        if self.country == "CL":
            # En Chile, millas no debe tener valor
            if cleaned_data.get("millas"):
                raise forms.ValidationError(
                    "El campo millas no puede usarse en documentos de Chile."
                )
        elif self.country == "US":
            # En USA, al menos uno de kilometraje o millas debe tener valor
            if not cleaned_data.get("kilometraje") and not cleaned_data.get("millas"):
                raise forms.ValidationError("Debe especificar al menos kilometraje o millas.")

        return cleaned_data

    def save(self, commit=True):
        """Override save para procesar datos JSON y crear líneas del documento"""
        documento = super().save(commit=commit)

        if commit:
            # Procesar datos JSON solo si el documento se guardó
            self._process_json_data(documento)

        return documento

    def _process_json_data(self, documento):
        """Procesa los datos JSON y crea las líneas del documento"""
        import json

        # Procesar repuestos
        repuestos_data = self.cleaned_data.get("repuestos_json", "[]")
        if repuestos_data:
            try:
                repuestos = json.loads(repuestos_data)
                for rep_data in repuestos:
                    if rep_data.get("codigo") or rep_data.get("nombre"):
                        from taller.models.lineas_documento import LineaRepuesto

                        LineaRepuesto.objects.create(
                            documento=documento,
                            codigo=rep_data.get("codigo", ""),
                            nombre=rep_data.get("nombre", ""),
                            cantidad=rep_data.get("cantidad", 1),
                            precio_unitario=rep_data.get("precio", 0),
                            descuento=rep_data.get("descuento", 0),
                        )
            except (json.JSONDecodeError, ValueError):
                pass  # Ignorar datos JSON inválidos

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
