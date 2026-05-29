from django import forms
from taller.models.configuracion import ConfiguracionEmpresa


class ConfiguracionEmpresaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = ["logo"]
