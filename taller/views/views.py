from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from taller.models.venta import Venta
from taller.models.repuesto import Repuesto
from taller.models.documento import Documento, ServicioDocumento

@login_required
def dashboard(request):
    empresa = request.user.empresa_admin
    hoy = timezone.now().date()
    semana_inicio = hoy - timedelta(days=hoy.weekday())
    mes_inicio = hoy.replace(day=1)

    ventas_hoy = Venta.objects.filter(empresa=empresa, fecha=hoy).aggregate(total=Sum('total'))['total'] or 0
    ventas_semana = Venta.objects.filter(empresa=empresa, fecha__gte=semana_inicio).aggregate(total=Sum('total'))['total'] or 0
    ventas_mes = Venta.objects.filter(empresa=empresa, fecha__gte=mes_inicio).aggregate(total=Sum('total'))['total'] or 0

    top_repuestos = Repuesto.objects.filter(empresa=empresa).annotate(
        vendidos=Sum('stock'),
        ganancia=Sum('precio_venta') - Sum('precio_compra')
    ).order_by('-vendidos')[:5]

    top_servicios = ServicioDocumento.objects.filter(empresa=empresa).values('nombre').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')[:5]

    actividad_usuarios = Documento.objects.filter(empresa=empresa).values('mecanico__nombre').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')[:3]

    ventas_mes_actual = ventas_mes
    dias_transcurridos = hoy.day
    dias_mes = 30
    ritmo_diario = ventas_mes_actual / dias_transcurridos if dias_transcurridos else 0
    prediccion = ritmo_diario * dias_mes

    alertas = []
    bajos = Repuesto.objects.filter(empresa=empresa, stock__lt=5)
    for r in bajos:
        alertas.append(f"El repuesto {r.nombre_repuesto} tiene bajo stock ({r.stock}). ¿Deseas crear una compra?")

    # Bienvenida dinámica
    inspecciones_pendientes = 0  # Puedes calcularlo según tu modelo
    ventas_por_cerrar = 0        # Puedes calcularlo según tu modelo
    documentos_vencidos = Documento.objects.filter(empresa=empresa, fecha__lt=hoy).count()
    bienvenida = f"¡Hola {request.user.username}! Hoy tu taller tiene {inspecciones_pendientes} inspecciones pendientes, {ventas_por_cerrar} ventas por cerrar y {documentos_vencidos} documento(s) vencido(s)."

    context = {
        'bienvenida': bienvenida,
        'ventas_hoy': ventas_hoy,
        'ventas_semana': ventas_semana,
        'ventas_mes': ventas_mes,
        'top_repuestos': top_repuestos,
        'top_servicios': top_servicios,
        'actividad_usuarios': actividad_usuarios,
        'prediccion': f"Si mantienes este ritmo, tu facturación mensual será ${int(prediccion):,}",
        'alertas': alertas,
    }
    return render(request, 'dashboard.html', context)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from taller.forms import EmpresaForm
from ..models import Empresa

@login_required
def editar_empresa(request):
    empresa, created = Empresa.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # o donde desees
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'empresa_form.html', {'form': form})

from django.core.mail import send_mail
from django.conf import settings
from .forms_trial import TrialForm
from .forms_subscription import PlanPagoForm
from taller.models.trial import TrialRegistro
from django.utils.crypto import get_random_string
import re

from django.shortcuts import render

def registro_unificado(request):
    mensaje = error = None
    tipo = request.POST.get('tipo_registro', 'trial')
    form = None
    if request.method == 'POST':
        if tipo == 'trial':
            form = TrialForm(request.POST)
            if form.is_valid():
                nombre = form.cleaned_data['nombre']
                email = form.cleaned_data['email']
                telefono = form.cleaned_data['telefono']
                codigo = get_random_string(12)
                TrialRegistro.objects.create(
                    nombre=nombre,
                    email=email,
                    telefono=telefono,
                    codigo=codigo,
                    ip=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                destinatarios = [email, 'suscripcion@atlantareciclajes.cl']
                send_mail(
                    'Tu código de instalación de E-Garage',
                    f'Hola {nombre},\n\nTu código de instalación seguro es: {codigo}\n\nGracias por probar E-Garage.\n',
                    settings.DEFAULT_FROM_EMAIL,
                    destinatarios,
                    fail_silently=False,
                )
                mensaje = '¡Código enviado! Revisa tu correo electrónico.'
                return render(request, 'registro_enviado.html', {'mensaje': mensaje, 'tipo': 'trial'})
        elif tipo == 'pago':
            form = PlanPagoForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                send_mail(
                    subject='Gracias por suscribirte a eGarage',
                    message=(
                        "Bienvenido a eGarage. Para activar tu plan, realiza la transferencia a:\n\n"
                        "Banco: Banco Ejemplo\n"
                        "Cuenta: 123456789\n"
                        "Rut: 11.111.111-1\n"
                        "Correo para enviar voucher: suscripcion@atlantareciclajes.cl\n\n"
                        "Una vez validado el pago, activaremos tu cuenta."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                mensaje = '¡Gracias por tu interés! Te enviamos los datos bancarios.'
                return render(request, 'registro_enviado.html', {'mensaje': mensaje, 'tipo': 'plan'})
    if not form:
        form = TrialForm() if tipo == 'trial' else PlanPagoForm()
    return render(request, 'registro.html', {'form': form, 'tipo': tipo})

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect

@login_required
def suscripcion_bloqueada(request):
    logout(request)
    return render(request, "bloqueada.html")

from django.shortcuts import render

def debug_cliente_autocomplete(request):
    return render(request, 'debug_autocomplete_cliente.html')

# --- Vistas de administración de suscripciones ---

from django.contrib.auth.decorators import user_passes_test, login_required
from django.utils.timezone import now
from django.shortcuts import get_object_or_404, redirect, render
from .models.empresa import Empresa
from .models.suscripcion import Suscripcion


# Vista protegida con métricas de suscripciones
@login_required
@user_passes_test(lambda u: u.is_staff)
def dashboard_suscripciones(request):
    # Para staff: mostrar todas las suscripciones (función administrativa)
    # Para usuarios normales: solo de su empresa
    if request.user.is_staff:
        suscripciones = Suscripcion.objects.all()  # Admin ve todas
    else:
        # Usuario normal solo ve suscripciones relacionadas con su empresa
        try:
            empresa = request.user.empresa
            suscripciones = Suscripcion.objects.filter(empresa=empresa)  # 🔒 FILTRO EMPRESA
        except:
            suscripciones = Suscripcion.objects.none()
    
    activas = sum(1 for s in suscripciones if s.activa and not s.esta_vencida())
    por_vencer = sum(1 for s in suscripciones if s.activa and s.por_vencer())
    vencidas = sum(1 for s in suscripciones if s.esta_vencida())
    return render(request, 'dashboard.htm', {
        'activas': activas,
        'por_vencer': por_vencer,
        'vencidas': vencidas,
    })

@user_passes_test(lambda u: u.is_staff)
def renovar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        empresa.fecha_inicio = now()
        empresa.suscripcion_activa = True
        empresa.save()
    return redirect('dashboard_suscripciones')


def landing_egarage(request):
    """Vista para servir la landing page de eGarage"""
    return render(request, 'landing_egarage.html')
