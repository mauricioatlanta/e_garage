from django import forms
from taller.models.clientes import Cliente

from taller.models.region_ciudad import TallerRegion, TallerCiudad
from taller.models.ubicacion import Estado as EstadoUSA, Ciudad as CiudadUSA


class ClienteForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        empresa = self.initial.get('empresa') or self.instance.empresa if hasattr(self.instance, 'empresa') else None
        if email and empresa:
            qs = Cliente.objects.filter(empresa=empresa, email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('email', 'Ya existe un cliente con este email para esta empresa.')
        return cleaned_data
    
    # Campos para Chile
    region = forms.ModelChoiceField(
        queryset=TallerRegion.objects.all(),
        required=False,
        widget=forms.Select(attrs={'id': 'id_region', 'class': 'form-control'}),
        empty_label="Seleccione Región"
    )
    ciudad = forms.ModelChoiceField(
        queryset=TallerCiudad.objects.none(),
        required=False,
        widget=forms.Select(attrs={'id': 'id_ciudad', 'class': 'form-control'}),
        empty_label="Seleccione Ciudad"
    )

    # Campos para USA
    estado_usa = forms.ModelChoiceField(
        queryset=EstadoUSA.objects.all(),
        required=False,
        widget=forms.Select(attrs={'id': 'id_estado_usa', 'class': 'form-control'}),
        empty_label="Select State"
    )
    ciudad_usa = forms.ModelChoiceField(
        queryset=CiudadUSA.objects.none(),
        required=False,
        widget=forms.Select(attrs={'id': 'id_ciudad_usa', 'class': 'form-control'}),
        empty_label="Select City"
    )
    zipcode = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zipcode'})
    )

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'direccion', 'region', 'ciudad', 'estado_usa', 'ciudad_usa', 'zipcode', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56912345678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)  # Almacenar empresa
        super().__init__(*args, **kwargs)

        # Debug logging
        print(f"🔍 [ClienteForm] empresa: {self.empresa}")
        if self.empresa:
            print(f"🔍 [ClienteForm] empresa.pais: {getattr(self.empresa, 'pais', 'NO_HAY_PAIS')}")
        else:
            print(f"🔍 [ClienteForm] NO HAY EMPRESA")

        # Chile: región/ciudad
        if 'region' in self.data and self.data.get('region') not in [None, '']:
            try:
                region_id = int(self.data.get('region'))
                self.fields['ciudad'].queryset = TallerCiudad.objects.filter(region_id=region_id)
            except (ValueError, TypeError):
                self.fields['ciudad'].queryset = TallerCiudad.objects.none()
        elif self.instance.pk and getattr(self.instance, 'region', None):
            self.fields['ciudad'].queryset = TallerCiudad.objects.filter(region=self.instance.region)
        else:
            self.fields['ciudad'].queryset = TallerCiudad.objects.none()

        # USA: estado/ciudad/zipcode
        if 'estado_usa' in self.data and self.data.get('estado_usa') not in [None, '']:
            try:
                estado_id = int(self.data.get('estado_usa'))
                self.fields['ciudad_usa'].queryset = CiudadUSA.objects.filter(estado_id=estado_id)
            except (ValueError, TypeError):
                self.fields['ciudad_usa'].queryset = CiudadUSA.objects.none()
        elif self.instance.pk and getattr(self.instance, 'estado_usa', None):
            self.fields['ciudad_usa'].queryset = CiudadUSA.objects.filter(estado=self.instance.estado_usa)
        else:
            self.fields['ciudad_usa'].queryset = CiudadUSA.objects.none()

        # Exponer el país como atributo público para el template
        pais = None
        if self.empresa:
            pais = self.empresa.pais
        elif self.instance.pk and hasattr(self.instance, 'empresa') and self.instance.empresa:
            pais = self.instance.empresa.pais
        self.pais = pais

        print(f"🔍 [ClienteForm] pais detectado: {self.pais}")

        # Ocultar campos según el país
        if self.pais == 'US':
            print(f"🔍 [ClienteForm] Ocultando campos de Chile para USA")
            self.fields['region'].widget = forms.HiddenInput()
            self.fields['ciudad'].widget = forms.HiddenInput()
        else:
            print(f"🔍 [ClienteForm] Ocultando campos de USA para Chile")
            self.fields['estado_usa'].widget = forms.HiddenInput()
            self.fields['ciudad_usa'].widget = forms.HiddenInput()
            self.fields['zipcode'].widget = forms.HiddenInput()

    def save(self, commit=True):
        obj = super().save(commit=False)
        
        # BLINDAJE MULTI-TENANT: SIEMPRE asignar empresa
        if self.empresa and not obj.empresa_id:
            obj.empresa = self.empresa
        
        if commit:
            obj.save()
            self.save_m2m()
        return obj

