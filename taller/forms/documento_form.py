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

    # Campo context: workshop / parts / mixed (para numeración y modo Parts)
    context = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        initial="workshop",
    )

    # Campos JSON para filas dinámicas
    repuestos_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    servicios_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    otros_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    payment_status = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
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
        self.request = kwargs.pop("request", None)

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

        # Configurar querysets filtrados por empresa
        if self.empresa:
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=self.empresa)
            self.fields["vehiculo"].queryset = Vehiculo.objects.filter(empresa=self.empresa)

            # Prefill vehículo: asegurar que esté en el queryset (evita "not a valid choice" en POST)
            prefill_vehiculo = ""
            if self.request:
                prefill_vehiculo = (
                    self.request.GET.get("prefill_vehiculo")
                    or self.request.GET.get("new_vehiculo_id")
                    or ""
                ).strip()
            if prefill_vehiculo and str(prefill_vehiculo).isdigit():
                self.fields["vehiculo"].queryset = self.fields[
                    "vehiculo"
                ].queryset | Vehiculo.objects.filter(empresa=self.empresa, pk=prefill_vehiculo)
            self.fields["tecnico_responsable"].queryset = self.empresa.tecnicos.all()

        # Configurar labels según el país
        self._configure_labels_by_country()

        # Configurar choices dinámicos
        self._configure_dynamic_choices()

        # Payment status: choices del modelo para que el template muestre select
        if "payment_status" in self.fields:
            self.fields["payment_status"].choices = Documento.PAYMENT_STATUS

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
        }

        for field_name, widget_id in widget_ids.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.setdefault("id", widget_id)

    def _configure_required_fields(self):
        """Configura qué campos son requeridos: solo los esenciales"""
        # Campos obligatorios: solo los esenciales
        # NOTA: 'numero' se autogenera en el modelo, NO es requerido en el form
        required_fields = ["tipo", "fecha_emision", "cliente"]

        # Modo Parts: vehiculo y tecnico no requeridos
        context_val = (
            (self.data.get("context") if self.data else None)
            or getattr(self.instance, "context", None)
            or "workshop"
        )
        if str(context_val).lower() == "parts":
            pass  # vehiculo y tecnico no requeridos (ya son required=False por defecto)
        else:
            # Workshop: tecnico opcional, vehiculo opcional (depende de config)
            pass

        # Marcar todos los campos como no requeridos por defecto
        for field_name in self.fields:
            self.fields[field_name].required = False

        # Marcar solo los campos esenciales como requeridos
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True

        # Modo Parts: vehiculo y tecnico nunca requeridos
        if str(context_val).lower() == "parts":
            if "vehiculo" in self.fields:
                self.fields["vehiculo"].required = False
            if "tecnico_responsable" in self.fields:
                self.fields["tecnico_responsable"].required = False

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

        # Placeholder por país (solo visual)
        attrs = dict(self.fields["kilometraje_ingreso"].widget.attrs)
        if self.instance and self.instance.pk and self.instance.vehiculo:
            try:
                kilometraje_actual = self.instance.vehiculo.kilometraje_actual
                if kilometraje_actual:
                    if self.country == "US":
                        attrs["placeholder"] = f"Current: {kilometraje_actual} mi"
                    else:
                        attrs["placeholder"] = f"Kilometraje actual: {kilometraje_actual} km"
            except Exception:
                pass

        if "placeholder" not in attrs:
            if self.country == "US":
                attrs["placeholder"] = "Miles"
            else:
                attrs["placeholder"] = "Kilometraje actual (km)"

        self.fields["kilometraje_ingreso"].widget.attrs.update(attrs)

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
            # En Chile, si hay vehículo, el kilometraje_ingreso debería ser requerido
            vehiculo = cleaned_data.get("vehiculo")
            if vehiculo and not cleaned_data.get("kilometraje_ingreso"):
                # Advertencia, no error - permitir crear sin kilometraje si es necesario
                pass
        elif self.country == "US":
            # En USA: requiere odómetro (miles) si hay vehículo
            vehiculo = cleaned_data.get("vehiculo")
            if vehiculo:
                odometro = cleaned_data.get("kilometraje_ingreso")
                millas = cleaned_data.get("millas")

                # Compatibilidad legacy: algunos templates/JS envían "kilometraje"
                if not odometro:
                    odometro = cleaned_data.get("kilometraje") or self.data.get("kilometraje")

                # Regla: en USA aceptamos odometro o millas (si todavía existe el campo millas)
                if not odometro and not millas:
                    raise forms.ValidationError(
                        "Debe especificar al menos kilometraje o millas cuando hay un vehículo."
                    )

                # Normalización: si viene odometro, lo dejamos en kilometraje_ingreso
                if odometro and not cleaned_data.get("kilometraje_ingreso"):
                    cleaned_data["kilometraje_ingreso"] = odometro

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

        # Compatibilidad legacy: algunos templates/JS envían "kilometraje"
        if kilometraje_ingreso is None:
            kilometraje_ingreso = self.cleaned_data.get("kilometraje") or self.data.get(
                "kilometraje"
            )

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
        """Procesa los datos JSON y crea las líneas del documento.
        En edición (documento.pk existe), borra líneas existentes antes de crear las nuevas.
        """
        import json

        # En edición: borrar líneas previas para evitar duplicados
        if documento.pk:
            documento.lineas_repuesto.all().delete()
            documento.lineas_servicio.all().delete()
            documento.lineas_otro_servicio.all().delete()

        # Procesar repuestos
        repuestos_data = self.cleaned_data.get("repuestos_json", "[]")
        if repuestos_data:
            try:
                repuestos = json.loads(repuestos_data)
                for rep_data in repuestos:
                    has_content = (
                        rep_data.get("codigo")
                        or rep_data.get("nombre")
                        or (
                            rep_data.get("source_type") == "CUSTOMER_SUPPLIED"
                            and rep_data.get("customer_part_description")
                        )
                    )
                    if has_content:
                        from taller.models.lineas_documento import LineaRepuesto

                        st = (rep_data.get("source_type") or "IN_STOCK").upper()
                        if st not in ("CUSTOMER_SUPPLIED", "IN_STOCK", "SOURCED"):
                            st = "IN_STOCK"
                        precio = 0 if st == "CUSTOMER_SUPPLIED" else rep_data.get("precio", 0)
                        cod = rep_data.get("codigo") or ""
                        nom = (
                            rep_data.get("nombre")
                            or (
                                rep_data.get("customer_part_description")
                                if st == "CUSTOMER_SUPPLIED"
                                else ""
                            )
                            or ""
                        )
                        LineaRepuesto.objects.create(
                            documento=documento,
                            codigo=cod or "CUST",
                            nombre=nom or "Customer part",
                            cantidad=rep_data.get("cantidad", 1),
                            precio_unitario=precio,
                            descuento=(
                                0 if st == "CUSTOMER_SUPPLIED" else rep_data.get("descuento", 0)
                            ),
                            source_type=st,
                            customer_part_description=rep_data.get("customer_part_description")
                            or None,
                            customer_part_notes=rep_data.get("customer_part_notes") or None,
                        )
            except (json.JSONDecodeError, ValueError):
                pass  # Ignorar datos JSON inválidos

        # Procesar servicios (SIN cantidad: forzamos cantidad=1)
        servicios_data = self.cleaned_data.get("servicios_json", "[]")
        if servicios_data:
            try:
                servicios = json.loads(servicios_data)
                for serv_data in servicios:
                    sid = serv_data.get("servicio_id")
                    if not sid:
                        continue
                    nombre = serv_data.get("nombre") or ""
                    if not nombre:
                        # Obtener nombre del Servicio o Service cuando no viene en JSON
                        try:
                            from taller.servicios.models import Servicio

                            s = Servicio.objects.filter(pk=sid).first()
                            if s:
                                nombre = getattr(s, "nombre", "") or str(s)
                            else:
                                from taller.models.catalogo_servicios import Service

                                svc = Service.objects.filter(pk=sid).first()
                                nombre = (
                                    getattr(svc, "service_code", "") or str(svc)
                                    if svc
                                    else "Servicio"
                                )
                        except Exception:
                            nombre = "Servicio"
                    from taller.models.lineas_documento import LineaServicio

                    LineaServicio.objects.create(
                        documento=documento,
                        servicio_id=sid,
                        nombre=nombre or "Servicio",
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
