# taller/documentos/forms_dal.py
from dal import autocomplete

from django import forms

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo


class DocumentoFormDAL(forms.ModelForm):
    """
    Formulario de documento usando DAL (Django Autocomplete Light)
    con forward para filtrar vehículos por cliente seleccionado.
    """

    class Meta:
        model = Documento
        fields = ["cliente", "vehiculo", "tipo", "fecha_emision", "tecnico_responsable"]
        widgets = {
            "cliente": autocomplete.ModelSelect2(
                url="autocomplete:cliente",
                attrs={"data-placeholder": "Buscar cliente..."},
            ),
            "vehiculo": autocomplete.ModelSelect2(
                url="autocomplete:vehiculo",
                forward=[
                    "cliente"
                ],  # <- Clave: filtra el listado por el cliente seleccionado
                attrs={"data-placeholder": "Buscar vehículo del cliente..."},
            ),
            "tecnico_responsable": autocomplete.ModelSelect2(
                url="autocomplete:tecnico",
                attrs={"data-placeholder": "Buscar técnico/vendedor..."},
            ),
        }

    def __init__(self, *args, **kwargs):
        # Opcional: inicializar querysets vacíos para que DAL mande a buscar vía endpoint
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = Cliente.objects.none()
        self.fields["vehiculo"].queryset = Vehiculo.objects.none()
