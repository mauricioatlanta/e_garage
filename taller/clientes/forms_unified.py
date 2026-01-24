# -*- coding: utf-8 -*-
"""
Formularios unificados para Cliente con Address

Convenciones:
- Usa modelo Address para billing/shipping
- Campos virtuales country/state/city para UI
- clean() crea Address automáticamente
- Reutiliza Estado/Ciudad existentes
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from taller.models.clientes import Cliente
from taller.models.ubicacion import Ciudad, Estado
from ubicacion.models import Address


class CustomerForm(forms.ModelForm):
    """
    Formulario unificado de Cliente con soporte para Address.

    Campos virtuales para UI:
    - country: Select de país
    - state: Código de estado (cargado por locations.js)
    - city: FK a Ciudad (cargado por locations.js)
    - line1, line2, postal_code: Campos de dirección

    El método clean() crea automáticamente el Address.
    """

    # === CAMPOS VIRTUALES PARA UI (no están en modelo Cliente) ===

    # País (para cascada en frontend)
    country = forms.ChoiceField(
        choices=(
            ("CL", "Chile"),
            ("US", "USA"),
            ("MX", "México"),
            ("BR", "Brasil"),
            ("PE", "Perú"),
            ("VE", "Venezuela"),
        ),
        required=False,
        label=_("Country"),
        widget=forms.Select(attrs={"id": "id_country", "class": "form-control"}),
    )

    # Estado/Departamento (código, se convierte a ID en clean())
    state = forms.CharField(
        required=False,
        label=_("State/Department"),
        widget=forms.TextInput(attrs={"id": "id_state", "class": "form-control"}),
    )

    # Ciudad (FK directa)
    city = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        required=False,
        label=_("City"),
        widget=forms.Select(attrs={"id": "id_city", "class": "form-control"}),
    )

    # Campos de dirección
    line1 = forms.CharField(
        required=False,
        label=_("Address Line 1"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Street, number, building")}
        ),
    )
    line2 = forms.CharField(
        required=False,
        label=_("Address Line 2"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Apartment, suite, unit (optional)")}
        ),
    )
    postal_code = forms.CharField(
        required=False,
        label=_("Postal Code"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Zipcode / CEP / Código Postal")}
        ),
    )

    class Meta:
        model = Cliente
        fields = [
            "nombre",
            "apellido",
            "telefono",
            "email",
            "tax_id_type",
            "tax_id",
            "giro",
            # Direcciones se setean en clean() automáticamente
            # 'billing_address' y 'shipping_address' no se muestran directamente
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("First name")}
            ),
            "apellido": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Last name (optional for companies)")}
            ),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Phone number (optional)")}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": _("Email (optional)")}),
            "tax_id_type": forms.Select(attrs={"class": "form-control"}),
            "tax_id": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Tax ID (required for billing)")}),
            "giro": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Business activity / Giro (required for billing)")}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        
        # === VALIDACIÓN CONDICIONAL: Solo nombre es obligatorio al inicio ===
        # Los campos de facturación son opcionales pero se validan cuando se intenta facturar
        
        # Nombre es obligatorio (ya está así en el modelo)
        self.fields["nombre"].required = True
        
        # Apellido es opcional (útil para empresas que usan Razón Social)
        self.fields["apellido"].required = False
        
        # Teléfono es opcional al inicio
        self.fields["telefono"].required = False
        
        # Email es opcional pero recomendado
        self.fields["email"].required = False
        
        # Campos de facturación: opcionales al inicio, requeridos para facturar
        self.fields["tax_id_type"].required = False
        self.fields["tax_id"].required = False
        self.fields["giro"].required = False
        
        # Dirección: opcional al inicio
        self.fields["country"].required = False
        self.fields["state"].required = False
        self.fields["city"].required = False
        self.fields["line1"].required = False

        # Si el cliente ya tiene billing_address, prellenar campos virtuales
        addr = getattr(self.instance, "billing_address", None)
        if addr and addr.city:
            st = addr.city.estado

            # Prellenar país
            self.fields["country"].initial = st.pais

            # Prellenar estado (código)
            self.fields["state"].initial = getattr(st, "codigo", "") or getattr(st, "code", "")

            # Prellenar ciudad (queryset filtrado)
            self.fields["city"].queryset = Ciudad.objects.filter(estado=st).order_by("nombre")
            self.fields["city"].initial = addr.city_id

            # Prellenar campos de dirección
            self.fields["line1"].initial = addr.line1
            self.fields["line2"].initial = addr.line2
            self.fields["postal_code"].initial = addr.postal_code

        # Auto-detectar país desde empresa si es nuevo cliente
        elif self.empresa and hasattr(self.empresa, "pais") and not self.instance.pk:
            pais = self.empresa.pais
            self.fields["country"].initial = pais

            # Auto-seleccionar tax_id_type según país
            tax_id_defaults = {
                "CL": "CL_RUT",
                "US": "US_EIN",
                "MX": "MX_RFC",
                "BR": "BR_CPF",
                "PE": "PE_RUC",
                "VE": "VE_RIF",
            }
            if "tax_id_type" in self.fields:
                self.fields["tax_id_type"].initial = tax_id_defaults.get(pais, "CL_RUT")

    def clean(self):
        """
        Validación y creación automática de Address.

        Si se proporcionan country, state, city y line1,
        crea un Address y lo asigna a billing_address.
        """
        cd = super().clean()

        country = (cd.get("country") or "").upper()
        state_code = (cd.get("state") or "").upper()
        city = cd.get("city")

        # Obtener line1 desde data (puede venir con diferentes nombres)
        line1 = self.data.get("line1", "").strip() or self.data.get("billing_line1", "").strip()

        # Si hay datos de dirección completos, crear Address
        if country and state_code and city and line1:
            try:
                # Verificar que la ciudad pertenezca al estado correcto
                if city.estado.pais != country:
                    raise forms.ValidationError(
                        {"city": _("La ciudad seleccionada no pertenece al país.")}
                    )

                # Crear Address (o actualizar si ya existe)
                if self.instance.billing_address:
                    # Actualizar dirección existente
                    addr = self.instance.billing_address
                    addr.line1 = line1
                    addr.line2 = self.data.get("line2", "").strip()
                    addr.city = city
                    addr.postal_code = self.data.get("postal_code", "").strip()
                    addr.save()
                else:
                    # Crear nueva dirección
                    addr = Address.objects.create(
                        line1=line1,
                        line2=self.data.get("line2", "").strip(),
                        city=city,
                        postal_code=self.data.get("postal_code", "").strip(),
                        company=self.empresa,  # Opcional: asociar a empresa
                    )

                # Asignar a cliente
                cd["billing_address"] = addr

            except Exception as e:
                raise forms.ValidationError(
                    {"city": _("Error al crear dirección: %(error)s") % {"error": str(e)}}
                )

        return cd

    def save(self, commit=True):
        """Guardar cliente con Address"""
        instance = super().save(commit=False)

        # BLINDAJE MULTI-TENANT: asignar empresa
        if self.empresa and not instance.empresa_id:
            instance.empresa = self.empresa

        if commit:
            instance.save()

        return instance


class CustomerAddressForm(forms.ModelForm):
    """
    Formulario simplificado solo para Address (billing/shipping).

    Útil para actualizar solo la dirección sin tocar otros datos del cliente.
    """

    # Campos virtuales para UI
    country = forms.ChoiceField(
        choices=(
            ("CL", "Chile"),
            ("US", "USA"),
            ("MX", "México"),
            ("BR", "Brasil"),
            ("PE", "Perú"),
            ("VE", "Venezuela"),
        ),
        required=True,
        label=_("Country"),
    )
    state_code = forms.CharField(
        required=True, label=_("State Code"), help_text=_("Código de estado (ej: LIM, SP, CA)")
    )

    class Meta:
        model = Address
        fields = ["line1", "line2", "city", "postal_code", "latitude", "longitude"]
        widgets = {
            "line1": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Street address")}
            ),
            "line2": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Apt, suite, unit (optional)")}
            ),
            "city": forms.Select(attrs={"class": "form-control", "id": "id_city"}),
            "postal_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Postal code")}
            ),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si es edición, prellenar campos virtuales
        if self.instance and self.instance.pk and self.instance.city:
            estado = self.instance.city.estado
            self.fields["country"].initial = estado.pais
            self.fields["state_code"].initial = getattr(estado, "codigo", "") or ""
            self.fields["city"].queryset = Ciudad.objects.filter(estado=estado)


class BillingDataForm(forms.ModelForm):
    """
    Formulario rápido para completar datos de facturación.
    
    Se usa en un pop-up cuando el mecánico intenta facturar
    y el cliente no tiene todos los datos requeridos.
    
    Solo incluye los campos mínimos necesarios para facturación:
    - tax_id (identificador tributario)
    - giro (actividad económica)
    - billing_address (dirección)
    """
    
    # Campos virtuales para dirección (igual que CustomerForm)
    country = forms.ChoiceField(
        choices=(
            ("CL", "Chile"),
            ("US", "USA"),
            ("MX", "México"),
            ("BR", "Brasil"),
            ("PE", "Perú"),
            ("VE", "Venezuela"),
        ),
        required=True,
        label=_("Country"),
        widget=forms.Select(attrs={"id": "id_billing_country", "class": "form-control"}),
    )
    
    state = forms.CharField(
        required=True,
        label=_("State/Department"),
        widget=forms.TextInput(attrs={"id": "id_billing_state", "class": "form-control"}),
    )
    
    city = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        required=True,
        label=_("City"),
        widget=forms.Select(attrs={"id": "id_billing_city", "class": "form-control"}),
    )
    
    line1 = forms.CharField(
        required=True,
        label=_("Address Line 1"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Street, number, building")}
        ),
    )
    
    line2 = forms.CharField(
        required=False,
        label=_("Address Line 2"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Apartment, suite, unit (optional)")}
        ),
    )
    
    postal_code = forms.CharField(
        required=False,
        label=_("Postal Code"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Zipcode / CEP / Código Postal")}
        ),
    )
    
    class Meta:
        model = Cliente
        fields = ["tax_id_type", "tax_id", "giro"]
        widgets = {
            "tax_id_type": forms.Select(attrs={"class": "form-control"}),
            "tax_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Tax ID")}
            ),
            "giro": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Business activity / Giro")}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        
        # Todos los campos son requeridos para facturación
        self.fields["tax_id_type"].required = True
        self.fields["tax_id"].required = True
        self.fields["giro"].required = True
        
        # Prellenar si el cliente ya tiene algunos datos
        if self.instance and self.instance.pk:
            # Prellenar tax_id si existe
            if self.instance.tax_id:
                self.fields["tax_id"].initial = self.instance.tax_id
            if self.instance.tax_id_type:
                self.fields["tax_id_type"].initial = self.instance.tax_id_type
            
            # Prellenar giro si existe
            if self.instance.giro:
                self.fields["giro"].initial = self.instance.giro
            
            # Prellenar dirección si existe
            addr = getattr(self.instance, "billing_address", None)
            if addr and addr.city:
                st = addr.city.estado
                self.fields["country"].initial = st.pais
                self.fields["state"].initial = getattr(st, "codigo", "") or getattr(st, "code", "")
                self.fields["city"].queryset = Ciudad.objects.filter(estado=st).order_by("nombre")
                self.fields["city"].initial = addr.city_id
                self.fields["line1"].initial = addr.line1
                self.fields["line2"].initial = addr.line2
                self.fields["postal_code"].initial = addr.postal_code
        else:
            # Auto-detectar país desde empresa
            if self.empresa and hasattr(self.empresa, "pais"):
                pais = self.empresa.pais
                self.fields["country"].initial = pais
                
                # Auto-seleccionar tax_id_type según país
                tax_id_defaults = {
                    "CL": "CL_RUT",
                    "US": "US_EIN",
                    "MX": "MX_RFC",
                    "BR": "BR_CPF",
                    "PE": "PE_RUC",
                    "VE": "VE_RIF",
                }
                self.fields["tax_id_type"].initial = tax_id_defaults.get(pais, "CL_RUT")
    
    def clean_tax_id(self):
        """Validar RUT/TAX_ID según el tipo seleccionado"""
        tax_id = self.cleaned_data.get("tax_id", "").strip()
        tax_id_type = self.cleaned_data.get("tax_id_type", "")
        
        if not tax_id:
            return tax_id
        
        # Validar según tipo usando validadores existentes
        from taller.utils.validators import validar_tax_id
        
        try:
            tax_id_validado = validar_tax_id(tax_id, tax_id_type)
            return tax_id_validado
        except Exception as e:
            raise forms.ValidationError(str(e))
    
    def clean(self):
        """Validación y creación automática de Address para facturación"""
        cd = super().clean()
        
        country = (cd.get("country") or "").upper()
        city_id = self.data.get("city") or cd.get("city")
        line1 = self.data.get("line1", "").strip()
        
        # Validar que todos los campos de dirección estén presentes
        if not (country and city_id and line1):
            raise forms.ValidationError(
                _("Todos los campos de dirección son requeridos para facturación.")
            )
        
        try:
            # Obtener el objeto City desde el ID
            from taller.models.ubicacion import Ciudad
            from taller.models.region_ciudad import TallerCiudad
            
            # Intentar primero con el modelo unificado (Ciudad)
            try:
                city = Ciudad.objects.get(id=city_id)
            except (Ciudad.DoesNotExist, ValueError):
                # Fallback: intentar con modelo legacy (TallerCiudad para Chile)
                try:
                    ciudad_legacy = TallerCiudad.objects.get(id=city_id)
                    # Convertir a modelo unificado si es necesario
                    # Por ahora, usar directamente si el sistema lo soporta
                    city = ciudad_legacy
                except TallerCiudad.DoesNotExist:
                    raise forms.ValidationError(
                        {"city": _("Ciudad no encontrada. Por favor, selecciona una comuna del listado.")}
                    )
            
            # Verificar que la ciudad pertenezca al país correcto
            # Para modelo unificado
            if hasattr(city, 'estado') and hasattr(city.estado, 'pais'):
                if city.estado.pais != country:
                    raise forms.ValidationError(
                        {"city": _("La ciudad seleccionada no pertenece al país.")}
                    )
            # Para modelo legacy (Chile)
            elif hasattr(city, 'region'):
                # Validar que sea de Chile si el país es CL
                if country != "CL":
                    raise forms.ValidationError(
                        {"city": _("La ciudad seleccionada no corresponde al país.")}
                    )
            
            # Crear o actualizar Address
            if self.instance.billing_address:
                addr = self.instance.billing_address
                addr.line1 = line1
                addr.line2 = self.data.get("line2", "").strip()
                # Para modelo legacy, necesitamos crear Address de forma diferente
                if hasattr(city, 'region'):
                    # Es modelo legacy, crear Address con ciudad del modelo unificado si existe
                    # O usar el modelo legacy directamente
                    addr.city = city  # Asumir que Address puede usar ambos modelos
                else:
                    addr.city = city
                addr.postal_code = self.data.get("postal_code", "").strip()
                addr.save()
            else:
                # Crear nueva dirección
                # Para modelo legacy, necesitamos mapear a modelo unificado
                if hasattr(city, 'region'):
                    # Buscar ciudad equivalente en modelo unificado
                    from taller.models.ubicacion import Estado, Ciudad
                    # Intentar encontrar estado correspondiente
                    estado = Estado.objects.filter(pais=country, nombre__icontains=city.region.nombre).first()
                    if estado:
                        ciudad_unificada = Ciudad.objects.filter(estado=estado, nombre__iexact=city.nombre).first()
                        if ciudad_unificada:
                            city = ciudad_unificada
                
                addr = Address.objects.create(
                    line1=line1,
                    line2=self.data.get("line2", "").strip(),
                    city=city,
                    postal_code=self.data.get("postal_code", "").strip(),
                    company=self.empresa,
                )
            
            cd["billing_address"] = addr
            
        except forms.ValidationError:
            raise
        except Exception as e:
            raise forms.ValidationError(
                {"city": _("Error al crear dirección: %(error)s") % {"error": str(e)}}
            )
        
        return cd
    
    def save(self, commit=True):
        """Guardar cliente con datos de facturación completos"""
        instance = super().save(commit=False)
        
        if self.cleaned_data.get("billing_address"):
            instance.billing_address = self.cleaned_data["billing_address"]
        
        if commit:
            instance.save()
        
        return instance
