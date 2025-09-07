from django.forms.models import inlineformset_factory

from taller.documentos.models import DetalleDocumento, Documento
from taller.forms.detalle import DetalleDocumentoForm

DetalleDocumentoFormSet = inlineformset_factory(
    Documento, DetalleDocumento, form=DetalleDocumentoForm, extra=1, can_delete=True
)
