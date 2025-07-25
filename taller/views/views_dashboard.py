from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Vehiculo, Documento, Venta
from .forms import VehiculoForm, DocumentoForm, VentaForm

@csrf_exempt
@require_POST
@login_required
def registrar_vehiculo(request):
    form = VehiculoForm(request.POST)
    if form.is_valid():
        vehiculo = form.save(commit=False)
        from taller.models.perfilusuario import PerfilUsuario
        perfil = PerfilUsuario.objects.get(user=request.user)
        vehiculo.empresa = perfil.empresa
        vehiculo.save()
        return JsonResponse({'success': True, 'msg': 'Vehículo registrado correctamente.'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@csrf_exempt
@require_POST
@login_required
def registrar_documento(request):
    form = DocumentoForm(request.POST)
    if form.is_valid():
        documento = form.save(commit=False)
        from taller.models.perfilusuario import PerfilUsuario
        perfil = PerfilUsuario.objects.get(user=request.user)
        documento.empresa = perfil.empresa
        documento.save()
        return JsonResponse({'success': True, 'msg': 'Documento emitido correctamente.'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@csrf_exempt
@require_POST
@login_required
def registrar_venta(request):
    form = VentaForm(request.POST)
    if form.is_valid():
        venta = form.save(commit=False)
        from taller.models.perfilusuario import PerfilUsuario
        perfil = PerfilUsuario.objects.get(user=request.user)
        venta.empresa = perfil.empresa
        venta.save()
        return JsonResponse({'success': True, 'msg': 'Venta registrada correctamente.'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)
