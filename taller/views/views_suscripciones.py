from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from taller.models.empresa import Empresa
from taller.models.comprobante_pago import ComprobantePago
from taller.forms.comprobante_form import ComprobantePagoForm


def suspension(request):
    """Vista de suspensión por suscripción vencida"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(request, "No se encontró información de empresa")
        return redirect('dashboard')
    
    # Si la suscripción está activa, redirigir al dashboard
    if not empresa.debe_bloquear:
        return redirect('dashboard')
    
    # Obtener comprobantes pendientes
    comprobantes_pendientes = ComprobantePago.objects.filter(
        empresa=empresa, 
        estado='pendiente'
    ).order_by('-fecha_subida')
    
    context = {
        'empresa': empresa,
        'comprobantes_pendientes': comprobantes_pendientes,
        'whatsapp_url': f"https://wa.me/56912345678?text=Hola, necesito renovar mi suscripción de eGarage para {empresa.nombre_taller}",
        'precios': {
            'basic': 15000,
            'premium': 25000,
            'enterprise': 45000,
        }
    }
    
    return render(request, 'suspension/suspension.html', context)


@login_required
def subir_comprobante(request):
    """Vista para subir comprobante de pago"""
    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(request, "No se encontró información de empresa")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ComprobantePagoForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.empresa = empresa
            comprobante.save()
            
            messages.success(request, 
                "Comprobante subido exitosamente. Te notificaremos cuando sea revisado.")
            return redirect('suspension')
    else:
        form = ComprobantePagoForm()
    
    context = {
        'form': form,
        'empresa': empresa,
    }
    
    return render(request, 'suspension/subir_comprobante.html', context)


@login_required
def estado_suscripcion(request):
    """Vista AJAX para obtener estado de suscripción"""
    try:
        empresa = request.user.empresa
        data = {
            'dias_restantes': empresa.dias_restantes,
            'fecha_expiracion': empresa.fecha_expiracion.strftime('%d/%m/%Y'),
            'estado': empresa.estado_suscripcion,
            'debe_mostrar_alerta': empresa.debe_mostrar_alerta(),
            'mensaje_alerta': empresa.get_mensaje_alerta(),
            'color_estado': empresa.color_estado,
        }
        return JsonResponse(data)
    except Empresa.DoesNotExist:
        return JsonResponse({'error': 'Empresa no encontrada'}, status=404)


def precios(request):
    """Vista pública con información de precios"""
    planes = {
        'basic': {
            'nombre': 'Plan Básico',
            'precio': 15000,
            'caracteristicas': [
                'Hasta 50 documentos por mes',
                'Gestión básica de clientes',
                'Reportes básicos',
                'Soporte por email',
            ]
        },
        'premium': {
            'nombre': 'Plan Premium',
            'precio': 25000,
            'caracteristicas': [
                'Documentos ilimitados',
                'Gestión completa de inventario',
                'Diagnóstico IA incluido',
                'Reportes avanzados',
                'Soporte prioritario',
            ]
        },
        'enterprise': {
            'nombre': 'Plan Empresarial',
            'precio': 45000,
            'caracteristicas': [
                'Todo del Plan Premium',
                'Multi-sucursales',
                'API personalizada',
                'Integración con sistemas externos',
                'Soporte dedicado 24/7',
            ]
        }
    }
    
    context = {
        'planes': planes,
        'whatsapp_contacto': "https://wa.me/56912345678?text=Hola, quiero información sobre los planes de eGarage",
    }
    
    return render(request, 'suspension/precios.html', context)
