from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from taller.models.pago import PagoPendiente


@staff_member_required
def aprobar_pago(request, pago_id):
    """
    Vista rápida para aprobar un pago desde el admin
    """
    pago = get_object_or_404(PagoPendiente, id=pago_id)
    
    if pago.estado != 'pendiente':
        messages.warning(request, f'Este pago ya fue {pago.estado}')
    else:
        pago.aprobar_pago(request.user)
        messages.success(
            request,
            f'✅ Pago aprobado. Suscripción de {pago.empresa.nombre_taller} activada por {pago.plan}.'
        )
    
    return redirect('admin:taller_pagopendiente_changelist')


@staff_member_required
def rechazar_pago(request, pago_id):
    """
    Vista rápida para rechazar un pago desde el admin
    """
    pago = get_object_or_404(PagoPendiente, id=pago_id)
    
    if pago.estado != 'pendiente':
        messages.warning(request, f'Este pago ya fue {pago.estado}')
    else:
        razon = 'Comprobante no válido o monto incorrecto'
        pago.rechazar_pago(request.user, razon)
        messages.warning(
            request,
            f'❌ Pago rechazado: {pago.empresa.nombre_taller}'
        )
    
    return redirect('admin:taller_pagopendiente_changelist')

