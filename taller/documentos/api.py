from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from taller.models.vehiculos import Vehiculo
from taller.models.repuesto import Repuesto
from taller.models.sequence import DocumentSequence

@login_required
def api_vehiculos_por_cliente(request):
    """API para obtener vehículos de un cliente específico"""
    cid = request.GET.get('cliente_id')
    qs = Vehiculo.objects.none()
    if cid:
        qs = Vehiculo.objects.filter(
            cliente_id=cid, 
            empresa=request.user.empresa
        ).values('id', 'patente', 'vin', 'marca__nombre', 'modelo__nombre')
    return JsonResponse(list(qs), safe=False)

@login_required
def api_repuesto_por_codigo(request):
    """API para obtener repuesto por código"""
    code = request.GET.get('codigo', '').strip()
    data = {}
    if code:
        try:
            r = Repuesto.objects.get(
                empresa=request.user.empresa, 
                part_number__iexact=code
            )
            data = {
                'id': r.id, 
                'nombre': r.nombre, 
                'precio_compra': str(r.precio_compra or 0), 
                'precio_venta': str(r.precio_venta or 0)
            }
        except Repuesto.DoesNotExist:
            data = {'id': None}
    return JsonResponse(data)

@login_required
def api_next_number(request):
    """API para obtener el siguiente número de documento"""
    tipo = request.GET.get('tipo', '').strip()
    data = {'numero': 'Se generará automáticamente'}
    
    if tipo:
        try:
            # Obtener el siguiente número sin incrementarlo aún
            sequence, created = DocumentSequence.objects.get_or_create(
                empresa=request.user.empresa,
                tipo=tipo,
                defaults={'current': 0}
            )
            
            # Generar el número con el siguiente valor
            next_num = sequence.current + 1
            prefix = {'OT': 'OT', 'FAC': 'F', 'PRES': 'P'}.get(tipo, 'D')
            numero = f"{prefix}{next_num:03d}"
            
            data = {'numero': numero}
        except Exception as e:
            print(f"Error generando número: {e}")
            data = {'numero': f'Se generará automáticamente ({tipo})'}
    
    return JsonResponse(data)
