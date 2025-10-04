from django import forms
from django.core.exceptions import ValidationError
from dal import autocomplete

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo


class DocumentoForm(forms.ModelForm):
    # Autocomplete: parte en none() para no cargar todo ni filtrar mal
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),
        widget=autocomplete.ModelSelect2(
            url="cl_autocomplete:cliente",  # se sobrescribe según país más abajo
            attrs={
                "data-placeholder": "🔍 Buscar cliente...",
                "data-minimum-input-length": 2,
            },
        ),
        required=False,
    )
    
    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.none(),
        widget=autocomplete.ModelSelect2(
            url="cl_autocomplete:vehiculo",  # se sobrescribe según país
            forward=["cliente"],  # DAL enviará el cliente elegido
            attrs={
                "data-placeholder": "🔍 Buscar vehículo...",
                "data-minimum-input-length": 1,
            },
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        # Extras
        self.user = kwargs.pop("user", None)
        self.empresa = kwargs.pop("empresa", None)
        self.country = kwargs.pop("country", "CL")
        super().__init__(*args, **kwargs)

        # Resolver empresa segura
        empresa = self.empresa or (getattr(self.user, "empresa", None))

        # Normaliza namespace de país para URLs DAL
        ns = "usa_autocomplete" if (self.country or "").upper() == "US" else "cl_autocomplete"
        self.fields["cliente"].widget.url = f"{ns}:cliente"
        self.fields["vehiculo"].widget.url = f"{ns}:vehiculo"

        # Labels y choices según país (solo si el campo existe en el form)
        if self.country.upper() == "US":
            if "tipo" in self.fields:
                self.fields["tipo"].label = "Document Type"
                self.fields["tipo"].choices = [
                    ("OT", "Work Order"),
                    ("PRES", "Estimate"),
                    ("REC", "Receipt/Invoice"),
                ]
            if "cliente" in self.fields: self.fields["cliente"].label = "Customer"
            if "vehiculo" in self.fields: self.fields["vehiculo"].label = "Vehicle"
            if "tecnico_responsable" in self.fields: self.fields["tecnico_responsable"].label = "Assigned Technician"
            if "fecha_emision" in self.fields: self.fields["fecha_emision"].label = "Issue Date"
            if "kilometraje" in self.fields: self.fields["kilometraje"].label = "Mileage"
            if "observaciones" in self.fields: self.fields["observaciones"].label = "Observations"
            if "pagado" in self.fields: self.fields["pagado"].label = "Paid"
            if "numero" in self.fields: self.fields["numero"].label = "Number"
            # Placeholders
            self.fields["cliente"].widget.attrs["data-placeholder"] = "🔍 Search customer..."
            self.fields["vehiculo"].widget.attrs["data-placeholder"] = "🔍 Search vehicle..."
        else:
            if "tipo" in self.fields:
                self.fields["tipo"].label = "Tipo de Documento"
                self.fields["tipo"].choices = [
                    ("OT", "Orden de Trabajo"),
                    ("PRES", "Presupuesto"),
                    ("REC", "Recibo/Boleta"),
                ]
            if "cliente" in self.fields: self.fields["cliente"].label = "Cliente"
            if "vehiculo" in self.fields: self.fields["vehiculo"].label = "Vehículo"
            if "tecnico_responsable" in self.fields: self.fields["tecnico_responsable"].label = "Técnico Responsable"
            if "fecha_emision" in self.fields: self.fields["fecha_emision"].label = "Fecha de Emisión"
            if "kilometraje" in self.fields: self.fields["kilometraje"].label = "Kilometraje"
            if "observaciones" in self.fields: self.fields["observaciones"].label = "Observaciones"
            if "pagado" in self.fields: self.fields["pagado"].label = "Pagado"
            if "numero" in self.fields: self.fields["numero"].label = "Número"
            # Placeholders
            self.fields["cliente"].widget.attrs["data-placeholder"] = "🔍 Buscar cliente..."
            self.fields["vehiculo"].widget.attrs["data-placeholder"] = "🔍 Buscar vehículo..."

        # Asegurar IDs únicos para JavaScript
        self.fields['tipo'].widget.attrs.setdefault("id", "id_tipo")
        self.fields['numero'].widget.attrs.setdefault("id", "id_numero")
        self.fields['fecha_emision'].widget.attrs.setdefault("id", "id_fecha_emision")
        self.fields['cliente'].widget.attrs.setdefault("id", "id_cliente")
        self.fields['vehiculo'].widget.attrs.setdefault("id", "id_vehiculo")
        self.fields['tecnico_responsable'].widget.attrs.setdefault("id", "id_tecnico_responsable")
        self.fields['kilometraje'].widget.attrs.setdefault("id", "id_kilometraje")
        self.fields['observaciones'].widget.attrs.setdefault("id", "id_observaciones")
        self.fields['pagado'].widget.attrs.setdefault("id", "id_pagado")

        # Filtra querysets por empresa (y asegura que la instancia actual sea visible)
        if empresa:
            if "tecnico_responsable" in self.fields:
                from taller.models.tecnico import Tecnico  # importar aquí para mantener este archivo limpio de modelos no usados
                self.fields["tecnico_responsable"].queryset = Tecnico.objects.filter(empresa=empresa)

            # Cliente: si hay instance o POST, incluye el seleccionado
            qs_cli = Cliente.objects.filter(empresa=empresa)
            cliente_id = self.data.get("cliente") or getattr(self.instance, "cliente_id", None)
            if cliente_id:
                try:
                    qs_cli = qs_cli | Cliente.objects.filter(pk=int(cliente_id), empresa=empresa)
                except (ValueError, TypeError):
                    pass
            self.fields["cliente"].queryset = qs_cli.distinct()

            # Vehículo: filtra por empresa y, si hay cliente (POST/instance), por cliente
            qs_veh = Vehiculo.objects.filter(empresa=empresa)
            if cliente_id:
                try:
                    qs_veh = qs_veh.filter(cliente_id=int(cliente_id))
                except (ValueError, TypeError):
                    qs_veh = Vehiculo.objects.none()
            else:
                # si venía un vehiculo en instance, inclúyelo para renderizar
                if getattr(self.instance, "vehiculo_id", None):
                    qs_veh = Vehiculo.objects.filter(pk=self.instance.vehiculo_id, empresa=empresa)
            self.fields["vehiculo"].queryset = qs_veh.distinct()
        else:
            # sin empresa -> nada visible
            self.fields["cliente"].queryset = Cliente.objects.none()
            self.fields["vehiculo"].queryset = Vehiculo.objects.none()
            if "tecnico_responsable" in self.fields:
                from taller.models.tecnico import Tecnico
                self.fields["tecnico_responsable"].queryset = Tecnico.objects.none()
    
    # Validación multi-tenant y coherencia cliente↔vehículo
    def clean(self):
        cleaned = super().clean()
        empresa = self.empresa or (getattr(self.user, "empresa", None))
        cliente = cleaned.get("cliente")
        vehiculo = cleaned.get("vehiculo")

        if empresa and cliente and cliente.empresa_id != empresa.id:
            raise ValidationError("El cliente no pertenece a tu empresa.")

        if empresa and vehiculo and vehiculo.empresa_id != empresa.id:
            raise ValidationError("El vehículo no pertenece a tu empresa.")

        if cliente and vehiculo and vehiculo.cliente_id != cliente.id:
            raise ValidationError("El vehículo seleccionado no pertenece al cliente.")

        return cleaned
    

    class Meta:
        model = Documento
        # 🔒 Lista blanca — ajusta a tus campos públicos editables
        fields = [
            "tipo",
            "numero", 
            "fecha_emision",
            "cliente",
            "vehiculo",
            "tecnico_responsable",
            "kilometraje",  # Campo existe en el modelo
            "observaciones",
            "pagado",
        ]
        widgets = {
            "numero": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "fecha_emision": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": "4"}),
        }


# LineaDocumentoForm removed - using formsets instead
