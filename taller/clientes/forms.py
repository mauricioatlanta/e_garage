from django import forms
from taller.models.clientes import Cliente
from taller.models.region_ciudad import TallerRegion, TallerCiudad

class ClienteForm(forms.ModelForm):
    region = forms.ModelChoiceField(queryset=TallerRegion.objects.all(), required=False)
    ciudad = forms.ModelChoiceField(queryset=TallerCiudad.objects.none(), required=False)

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'direccion', 'region', 'ciudad', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'region' in self.data and self.data.get('region'):
            try:
                region_id = int(self.data.get('region'))
                self.fields['ciudad'].queryset = TallerCiudad.objects.filter(region_id=region_id)
            except (ValueError, TypeError):
                self.fields['ciudad'].queryset = TallerCiudad.objects.none()
        elif self.instance.pk and self.instance.region:
            self.fields['ciudad'].queryset = TallerCiudad.objects.filter(region=self.instance.region)
        else:
            self.fields['ciudad'].queryset = TallerCiudad.objects.none()
