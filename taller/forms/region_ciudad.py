from django import forms
from dal import autocomplete
	from taller.models.region_ciudad import TallerRegion, TallerCiudad

# Alias para compatibilidad con el resto del código
Region = TallerRegion
Ciudad = TallerCiudad


class UbicacionForm(forms.Form):
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        widget=autocomplete.ModelSelect2(url='region-autocomplete'),
        label="Región"
    )
    ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        widget=autocomplete.ModelSelect2(
            url='ciudad-autocomplete',
            forward=['region']
        ),
        label="Ciudad"
    )
