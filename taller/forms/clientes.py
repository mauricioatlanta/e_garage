from django import forms
from django.forms import ModelForm, TextInput, EmailInput, Select
from taller.models.clientes import Cliente
from taller.models.region_ciudad import TallerRegion, TallerCiudad


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].queryset = TallerRegion.objects.all()
        self.fields['ciudad'].queryset = TallerCiudad.objects.none()

        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['ciudad'].queryset = TallerCiudad.objects.filter(region_id=region_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.region:
            self.fields['ciudad'].queryset = TallerCiudad.objects.filter(region=self.instance.region)
        elif self.initial.get('region'):
            self.fields['ciudad'].queryset = TallerCiudad.objects.filter(region=self.initial['region'])

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        return nombre.capitalize() if nombre else nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '')
        return apellido.capitalize() if apellido else apellido

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion', '')
        return direccion.title() if direccion else direccion

