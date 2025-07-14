
from django.shortcuts import get_object_or_404, render
from .models import Documento

def ver_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    detalles = documento.detalle_set.all()

    subtotal = sum(d.precio_venta or 0 for d in detalles)
    iva = subtotal * 0.19
    total = subtotal + iva

    return render(request, 'taller/documentos/ver_documento.html', {
        'documento': documento,
        'detalles': detalles,
        'subtotal': subtotal,
        'iva': iva,
        'total': total
    })
